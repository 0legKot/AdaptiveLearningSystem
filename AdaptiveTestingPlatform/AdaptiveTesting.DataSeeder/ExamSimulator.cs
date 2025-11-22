using AdaptiveTesting.Domain.Entities;
using AdaptiveTesting.Infrastructure.Persistence;
using Bogus;
using Microsoft.EntityFrameworkCore;
using System.Net.Http.Json;

public class ExamSimulator {
    private readonly AppDbContext _db;
    private readonly Faker _faker = new();
    private readonly Random _rnd = new();
    private readonly HttpClient _mlClient;

    public ExamSimulator(AppDbContext db) {
        _db = db;
        _mlClient = new HttpClient { BaseAddress = new Uri("http://127.0.0.1:8000/") };
    }

    public async Task RunSimulationAsync(int studentCount) {
        Console.WriteLine($"Simulating {studentCount} students...");

        await _db.AnswerLogs.ExecuteDeleteAsync();
        await _db.TestSessions.ExecuteDeleteAsync();
        await _db.UserTopicStates.ExecuteDeleteAsync();
        await _db.Users.ExecuteDeleteAsync();

        var questions = await _db.Questions.ToListAsync();
        if (!questions.Any()) { Console.WriteLine("No questions!"); return; }

        var archetypes = StudentFactory.GetArchetypes();
        var users = new List<User>();
        var allSessions = new List<TestSession>();
        var allLogs = new List<AnswerLog>();
        var allStates = new List<UserTopicState>();

        for (int i = 0; i < studentCount; i++) {
            var arch = archetypes[i % archetypes.Count];
            int clusterLabel = arch.IsCheater ? 0 : (arch.Role.Contains("Junior") ? 1 : 2);

            var user = new User {
                Id = Guid.NewGuid(),
                FullName = $"{_faker.Name.FullName()} ({arch.Role})",
                Role = "Student",
                ClusterLabel = clusterLabel
            };
            users.Add(user);

            var userStates = new Dictionary<string, UserTopicState>();

            for (int s = 0; s < 50; s++) {
                var session = new TestSession {
                    Id = Guid.NewGuid(),
                    UserId = user.Id,
                    StartedAt = DateTime.Now.AddDays(-(5 - s)),
                    FinishedAt = DateTime.Now.AddDays(-(5 - s)).AddMinutes(10),
                    IsSuspicious = false
                };

                var sessionQuestions = questions.OrderBy(x => _rnd.Next()).Take(10).ToList();
                bool sessionHasAnomaly = false;

                foreach (var q in sessionQuestions) {
                    bool isCorrect;
                    int timeSpent;
                    int focusLost = 0;

                    if (arch.IsCheater) {

                        isCorrect = !q.Text.Contains("[ANOMALY]") && _rnd.NextDouble() > 0.01;
                        timeSpent = _rnd.Next(2000, 5000);
                        focusLost = _rnd.Next(1, 6);
                    } else {
                        if (q.Text.Contains("[ANOMALY]")) {

                            isCorrect = false;

                            timeSpent = _rnd.Next(15000, 40000);
                        } else {

                            double userSkill = arch.SkillMap.GetValueOrDefault(q.Topic, -1.0);
                            double z = userSkill - q.Difficulty;
                            double prob = 1.0 / (1.0 + Math.Exp(-z));

                            isCorrect = _rnd.NextDouble() < prob;

                            timeSpent = _rnd.Next(15000, 45000);

                            if (q.Difficulty > 0) timeSpent += _rnd.Next(5000, 15000);
                        }

                        focusLost = _rnd.NextDouble() > 0.9 ? 1 : 0;
                    }

                    bool isFlagged = await CallMlAntiCheat(timeSpent, focusLost);
                    if (isFlagged) sessionHasAnomaly = true;

                    var log = new AnswerLog {
                        Id = Guid.NewGuid(),
                        SessionId = session.Id,
                        QuestionId = q.Id,
                        IsCorrect = isCorrect,
                        TimeSpentMs = timeSpent,
                        FocusLostEvents = focusLost
                    };
                    allLogs.Add(log);

                    if (!userStates.ContainsKey(q.Topic)) {
                        var newState = new UserTopicState { Id = Guid.NewGuid(), UserId = user.Id, TopicName = q.Topic, AbilityTheta = 0.0, LastUpdated = session.StartedAt };
                        userStates[q.Topic] = newState;
                        allStates.Add(newState);
                    }
                    var st = userStates[q.Topic];
                    st.AbilityTheta = await CallMlBkt(st.AbilityTheta, isCorrect, q.Difficulty, q.Topic);
                    st.LastUpdated = session.StartedAt;
                }

                session.IsSuspicious = sessionHasAnomaly;
                allSessions.Add(session);
            }
            Console.Write(".");
        }

        Console.WriteLine("\nSaving to DB...");
        await _db.Users.AddRangeAsync(users);
        await _db.TestSessions.AddRangeAsync(allSessions);
        await _db.AnswerLogs.AddRangeAsync(allLogs);
        await _db.UserTopicStates.AddRangeAsync(allStates);
        await _db.SaveChangesAsync();

        await AnalyzeQuestionsQuality(allLogs, questions);
    }

    private async Task AnalyzeQuestionsQuality(List<AnswerLog> logs, List<Question> questions) {
        Console.WriteLine("\nChecking Question Quality...");
        var stats = logs.GroupBy(l => l.QuestionId)
            .Select(g => {
                var q = questions.FirstOrDefault(x => x.Id == g.Key);
                return new {
                    question_id = g.Key.ToString(),
                    difficulty_declared = q?.Difficulty ?? 0,
                    avg_time_spent = g.Average(x => x.TimeSpentMs),
                    error_rate = (double)g.Count(x => !x.IsCorrect) / g.Count()
                };
            }).ToList();

        try {
            var response = await _mlClient.PostAsJsonAsync("/analytics/analyze-questions", stats);
            var results = await response.Content.ReadFromJsonAsync<List<QualityResult>>();
            var anomalies = results?.Where(r => r.cluster_name.Contains("Anomaly") || r.cluster_name.Contains("Broken")).ToList();

            Console.WriteLine($"Total Questions: {results?.Count}");
            Console.WriteLine($"Anomalies Found: {anomalies?.Count}");
            foreach (var a in anomalies ?? new()) Console.WriteLine($" -> {a.cluster_name} (ID: {a.question_id})");
        } catch { }
    }

    private async Task<double> CallMlBkt(double p_known, bool is_correct, double difficulty, string topic) {
        try {
            var payload = new { p_known, is_correct, difficulty, total_options = 4, topic };
            var response = await _mlClient.PostAsJsonAsync("/adaptive/predict-knowledge", payload);
            var result = await response.Content.ReadFromJsonAsync<BktResponse>();
            return result?.new_theta ?? p_known;
        } catch { return p_known; }
    }

    private async Task<bool> CallMlAntiCheat(int timeMs, int focusLost) {
        try {
            var payload = new { time_spent_ms = timeMs, focus_lost_count = focusLost };
            var response = await _mlClient.PostAsJsonAsync("/security/detect-cheating", payload);
            var result = await response.Content.ReadFromJsonAsync<CheatingResponse>();
            return result?.is_suspicious ?? false;
        } catch { return false; }
    }

    private record BktResponse(double new_theta);
    private record CheatingResponse(bool is_suspicious);
    private record QualityResult(string question_id, string cluster_name);
}