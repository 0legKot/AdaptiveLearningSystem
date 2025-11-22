namespace AdaptiveTesting.Domain.Interfaces;

public interface IMlService {
    Task<double> PredictKnowledgeAsync(double currentTheta, bool isCorrect);
    Task<bool> IsSuspiciousBehaviorAsync(int timeSpentMs, int focusLostCount);

    // Виправлено: Тепер тип StudentClusterData існує
    Task<Dictionary<Guid, int>> ClusterStudentsAsync(List<StudentClusterData> students);

    // Нові методи
    Task<int> PredictFinalScoreAsync(double avgTime, double currentScore, int focusLost);
    Task<Guid?> FindSimilarQuestionAsync(string failedQuestionText, List<QuestionCandidate> candidates);
    Task<List<MiningRule>> GetMiningRulesAsync(List<StudentHistoryItem> history);
}

// --- ВСІ DTO ДЛЯ ML ---

// 1. Для кластеризації (те, чого не вистачало)
public record StudentClusterData(Guid StudentId, double AvgTime, double AvgScore);

// 2. Для NLP
public record QuestionCandidate(Guid id, string text);

// 3. Для Data Mining
public record StudentHistoryItem(string student_id, List<string> failed_topics);
public record MiningRule(string rule, double confidence);