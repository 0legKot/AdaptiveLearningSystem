namespace AdaptiveTesting.Domain.Interfaces;

public interface IMlService {
    Task<double> PredictKnowledgeAsync(double currentTheta, bool isCorrect);
    Task<bool> IsSuspiciousBehaviorAsync(int timeSpentMs, int focusLostCount);
    Task<Dictionary<Guid, int>> ClusterStudentsAsync(List<StudentClusterData> students);
    Task<int> PredictFinalScoreAsync(double avgTime, double currentScore, int focusLost);
    Task<Guid?> FindSimilarQuestionAsync(string failedQuestionText, List<QuestionCandidate> candidates);
    Task<List<MiningRule>> GetMiningRulesAsync(List<StudentHistoryItem> history);
    Task<List<QuestionQualityDto>> AnalyzeQuestionQualityAsync(List<QuestionStatsDto> stats);
    Task<Dictionary<string, double>> GetFeatureImportanceAsync();
}

public record StudentClusterData(Guid StudentId, double AvgTime, double AvgScore);
public record QuestionCandidate(Guid id, string text);
public record StudentHistoryItem(string student_id, List<string> failed_topics);
public record MiningRule(string rule, double confidence);
public record QuestionQualityDto(string question_id, string cluster_name);
public record QuestionStatsDto(string question_id, double difficulty_declared, double avg_time_spent, double error_rate);