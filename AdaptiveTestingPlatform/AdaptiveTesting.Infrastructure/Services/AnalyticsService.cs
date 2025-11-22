using AdaptiveTesting.Domain.Entities;
using AdaptiveTesting.Domain.Interfaces;
using AdaptiveTesting.Infrastructure.Persistence;
using Microsoft.EntityFrameworkCore;

namespace AdaptiveTesting.Infrastructure.Services;

public class AnalyticsService {
    private readonly AppDbContext _db;
    private readonly IMlService _mlService;

    public AnalyticsService(AppDbContext db, IMlService mlService) {
        _db = db;
        _mlService = mlService;
    }

    public async Task<StudentDashboardDto> GetStudentStatsAsync(Guid userId) {
        var topicStates = await _db.UserTopicStates
            .Where(s => s.UserId == userId)
            .ToListAsync();

        var sessions = await _db.TestSessions
            .Include(s => s.Answers)
            .Where(s => s.UserId == userId)
            .OrderByDescending(s => s.StartedAt)
            .ToListAsync();

        var user = await _db.Users.FindAsync(userId);

        var skills = topicStates.Select(t => new SkillDto {
            Topic = t.TopicName,
            Score = NormalizeTheta(t.AbilityTheta),
            RawTheta = t.AbilityTheta
        }).ToList();

        double avgTime = 0;
        double currentAvgScore = 0;
        int totalFocusLost = 0;

        if (sessions.Any()) {
            var allAnswers = sessions.SelectMany(s => s.Answers).ToList();

            if (allAnswers.Any()) {
                avgTime = allAnswers.Average(a => a.TimeSpentMs);
                currentAvgScore = (double)allAnswers.Count(a => a.IsCorrect) / allAnswers.Count * 100.0;
                totalFocusLost = allAnswers.Sum(a => a.FocusLostEvents);
            }
        }

        int predictedScore = await _mlService.PredictFinalScoreAsync(avgTime, currentAvgScore, totalFocusLost);

        return new StudentDashboardDto {
            StudentName = user?.FullName ?? "Unknown",
            ClusterLabel = user?.ClusterLabel ?? -1,
            PredictedScore = predictedScore,
            Skills = skills,
            RecentSessions = sessions.Take(5).Select(s => new SessionSummaryDto {
                Date = s.StartedAt,
                IsSuspicious = s.IsSuspicious,
                Score = s.Answers.Any() ? (int)((double)s.Answers.Count(a => a.IsCorrect) / s.Answers.Count * 100) : 0
            }).ToList(),
            Recommendations = GenerateRecommendations(skills)
        };
    }

    private double NormalizeTheta(double theta) {
        double sigmoid = 1.0 / (1.0 + Math.Exp(-theta));
        return Math.Round(sigmoid * 100, 1);
    }

    private List<string> GenerateRecommendations(List<SkillDto> skills) {
        var recs = new List<string>();
        foreach (var s in skills.OrderBy(x => x.Score)) {
            if (s.Score < 40)
                recs.Add($"⚠️ **{s.Topic}**: Критично низький рівень.");
            else if (s.Score < 70)
                recs.Add($"ℹ️ **{s.Topic}**: Є прогалини, варто повторити.");
            else
                recs.Add($"✅ **{s.Topic}**: Чудовий результат!");
        }
        if (!skills.Any()) recs.Add("Немає даних для рекомендацій.");
        return recs;
    }
}

public class StudentDashboardDto {
    public string StudentName { get; set; }
    public int ClusterLabel { get; set; }
    public int PredictedScore { get; set; }
    public List<SkillDto> Skills { get; set; }
    public List<SessionSummaryDto> RecentSessions { get; set; }
    public List<string> Recommendations { get; set; }
}

public class SkillDto {
    public string Topic { get; set; }
    public double Score { get; set; }
    public double RawTheta { get; set; }
}

public class SessionSummaryDto {
    public DateTime Date { get; set; }
    public bool IsSuspicious { get; set; }
    public int Score { get; set; }
}