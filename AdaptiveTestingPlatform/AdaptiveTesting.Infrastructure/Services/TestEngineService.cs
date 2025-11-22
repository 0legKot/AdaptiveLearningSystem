using AdaptiveTesting.Domain.Entities;
using AdaptiveTesting.Domain.Interfaces;
using AdaptiveTesting.Infrastructure.Persistence;
using Microsoft.EntityFrameworkCore;

namespace AdaptiveTesting.Infrastructure.Services;

public class TestEngineService {
    private readonly AppDbContext _db;
    private readonly IMlService _mlService;

    public TestEngineService(AppDbContext db, IMlService mlService) {
        _db = db;
        _mlService = mlService;
    }

    // 1. Початок сесії
    public async Task<TestSession> StartSessionAsync(Guid userId) {
        var session = new TestSession {
            Id = Guid.NewGuid(),
            UserId = userId,
            StartedAt = DateTime.Now
        };
        _db.TestSessions.Add(session);
        await _db.SaveChangesAsync();
        return session;
    }

    public async Task<Question?> GetNextQuestionAsync(Guid userId, Guid sessionId) {
        var answeredIds = await _db.AnswerLogs
            .Where(l => l.SessionId == sessionId)
            .Select(l => l.QuestionId)
            .ToListAsync();

        if (answeredIds.Count >= 10) return null;

        var userState = await _db.UserTopicStates
            .Where(s => s.UserId == userId)
            .OrderByDescending(s => s.LastUpdated)
            .FirstOrDefaultAsync();

        double currentTheta = userState?.AbilityTheta ?? 0.0;

        // --- NLP LOGIC START ---
        // Перевіряємо, чи остання відповідь була неправильною
        var lastLog = await _db.AnswerLogs
            .Include(a => a.Question)
            .Where(l => l.SessionId == sessionId)
            .OrderByDescending(l => l.Id) // Останній запис
            .FirstOrDefaultAsync();

        Question? nextQuestion = null;

        if (lastLog != null && !lastLog.IsCorrect && lastLog.Question != null) {
            // Якщо помилився -> шукаємо схоже питання через Python (NLP)
            var candidates = await _db.Questions
                .Where(q => !answeredIds.Contains(q.Id))
                .Select(q => new Domain.Interfaces.QuestionCandidate(q.Id, q.Text))
                .ToListAsync();

            // Викликаємо ML
            var similarId = await _mlService.FindSimilarQuestionAsync(lastLog.Question.Text, candidates);

            if (similarId.HasValue) {
                nextQuestion = await _db.Questions.FindAsync(similarId.Value);
            }
        }
        // --- NLP LOGIC END ---

        // Якщо NLP нічого не знайшов або відповідь була правильною -> стандартна логіка (по складності)
        if (nextQuestion == null) {
            nextQuestion = await _db.Questions
                .Where(q => !answeredIds.Contains(q.Id))
                .OrderBy(q => Math.Abs(q.Difficulty - currentTheta))
                .FirstOrDefaultAsync();
        }

        return nextQuestion;
    }

    public async Task SubmitAnswerAsync(Guid sessionId, Guid questionId, int optionIndex, int timeSpentMs, int focusLost) {
        var session = await _db.TestSessions.Include(s => s.User).FirstOrDefaultAsync(s => s.Id == sessionId);
        var question = await _db.Questions.FindAsync(questionId);

        if (session == null || question == null) return;

        bool isCorrect = question.CorrectOptionIndex == optionIndex;

        var log = new AnswerLog {
            Id = Guid.NewGuid(),
            SessionId = sessionId,
            QuestionId = questionId,
            IsCorrect = isCorrect,
            TimeSpentMs = timeSpentMs,
            FocusLostEvents = focusLost
        };
        _db.AnswerLogs.Add(log);

        var state = await _db.UserTopicStates
            .FirstOrDefaultAsync(s => s.UserId == session.UserId && s.TopicName == question.Topic);

        if (state == null) {
            state = new UserTopicState { UserId = session.UserId, TopicName = question.Topic, AbilityTheta = 0.5 };
            _db.UserTopicStates.Add(state);
        }

        int optionsCount = 4;
        if (!string.IsNullOrEmpty(question.OptionsJson)) {
            try {
                var opts = System.Text.Json.JsonSerializer.Deserialize<List<string>>(question.OptionsJson);
                optionsCount = opts?.Count ?? 4;
            } catch { }
        }

        double newTheta = await _mlService.PredictKnowledgeAsync(
            state.AbilityTheta,
            isCorrect,
            question.Difficulty,
            optionsCount,
            question.Topic
        );

        state.AbilityTheta = newTheta;
        state.LastUpdated = DateTime.Now;

        bool isSuspicious = await _mlService.IsSuspiciousBehaviorAsync(timeSpentMs, focusLost);
        if (isSuspicious) {
            session.IsSuspicious = true;
        }

        await _db.SaveChangesAsync();
    }

    public async Task FinishSessionAsync(Guid sessionId) {
        var session = await _db.TestSessions.FindAsync(sessionId);
        if (session != null) {
            session.FinishedAt = DateTime.Now;
            await _db.SaveChangesAsync();
        }
    }
}