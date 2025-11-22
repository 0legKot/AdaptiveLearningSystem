using System.Net.Http.Json;
using AdaptiveTesting.Domain.Interfaces;

namespace AdaptiveTesting.Infrastructure.Services;

public class PythonMlClient : IMlService {
    private readonly HttpClient _httpClient;

    public PythonMlClient(HttpClient httpClient) {
        _httpClient = httpClient;
        _httpClient.BaseAddress = new Uri("http://127.0.0.1:8000/");
    }
    public async Task<double> PredictKnowledgeAsync(double currentTheta, bool isCorrect) {
        try {
            var payload = new { p_known = currentTheta == 0 ? 0.5 : currentTheta, is_correct = isCorrect };
            var response = await _httpClient.PostAsJsonAsync("/predict-knowledge", payload);

            if (!response.IsSuccessStatusCode) return currentTheta;

            var result = await response.Content.ReadFromJsonAsync<BktResponse>();
            return result?.new_theta ?? currentTheta;
        } catch {
            return currentTheta;
        }
    }

    public async Task<bool> IsSuspiciousBehaviorAsync(int timeSpentMs, int focusLostCount) {
        try {
            var payload = new { time_spent_ms = timeSpentMs, focus_lost_count = focusLostCount };
            var response = await _httpClient.PostAsJsonAsync("/detect-cheating", payload);

            var result = await response.Content.ReadFromJsonAsync<CheatingResponse>();
            return result?.is_suspicious ?? false;
        } catch {
            return false;
        }
    }

    public async Task<Dictionary<Guid, int>> ClusterStudentsAsync(List<StudentClusterData> students) {
        try {
            var payload = students.Select(s => new {
                student_id = s.StudentId.ToString(),
                avg_time = s.AvgTime,
                avg_score = s.AvgScore
            }).ToList();

            var response = await _httpClient.PostAsJsonAsync("/cluster-students", payload);
            var result = await response.Content.ReadFromJsonAsync<List<ClusterResult>>();

            if (result == null) return new Dictionary<Guid, int>();

            return result.ToDictionary(k => k.student_id, v => v.cluster_id);
        } catch {
            return new Dictionary<Guid, int>();
        }
    }


    // --- НОВА РЕАЛІЗАЦІЯ ---

    public async Task<int> PredictFinalScoreAsync(double avgTime, double currentScore, int focusLost) {
        try {
            var payload = new { avg_time_per_question = avgTime, current_score_percent = currentScore, focus_lost_count = focusLost };
            var response = await _httpClient.PostAsJsonAsync("/prediction/final-score", payload);

            var result = await response.Content.ReadFromJsonAsync<PredictionResponse>();
            return result?.predicted_score ?? 0;
        } catch {
            return 0; // Fallback
        }
    }

    public async Task<Guid?> FindSimilarQuestionAsync(string failedText, List<QuestionCandidate> candidates) {
        try {
            var payload = new {
                failed_question_text = failedText,
                candidate_questions = candidates.Select(c => new { id = c.id.ToString(), text = c.text }).ToList()
            };

            var response = await _httpClient.PostAsJsonAsync("/nlp/similar-question", payload);
            var result = await response.Content.ReadFromJsonAsync<NlpResponse>();

            if (result?.recommended_id != null && Guid.TryParse(result.recommended_id, out var guid)) {
                return guid;
            }
            return null;
        } catch {
            return null;
        }
    }

    public async Task<List<MiningRule>> GetMiningRulesAsync(List<StudentHistoryItem> history) {
        try {
            var response = await _httpClient.PostAsJsonAsync("/mining/rules", history);
            if (!response.IsSuccessStatusCode) return new List<MiningRule>();

            var result = await response.Content.ReadFromJsonAsync<List<MiningRuleDto>>();
            return result?.Select(r => new MiningRule(r.rule, r.confidence)).ToList() ?? new();
        } catch {
            return new List<MiningRule>();
        }
    }

    public async Task<List<QuestionQualityDto>> AnalyzeQuestionQualityAsync(List<QuestionStatsDto> stats) {
        try {
            var response = await _httpClient.PostAsJsonAsync("/analytics/analyze-questions", stats);
            return await response.Content.ReadFromJsonAsync<List<QuestionQualityDto>>() ?? new();
        } catch { return new(); }
    }

    public async Task<Dictionary<string, double>> GetFeatureImportanceAsync() {
        try {
            return await _httpClient.GetFromJsonAsync<Dictionary<string, double>>("/prediction/factors-importance") ?? new();
        } catch { return new(); }
    }

    // Private Response DTOs
    private record PredictionResponse(int predicted_score);
    private record NlpResponse(string? recommended_id, double similarity);
    private record MiningRuleDto(string rule, double confidence);
    private record BktResponse(double new_theta);
    private record CheatingResponse(bool is_suspicious);
    private record ClusterResult(Guid student_id, int cluster_id);
}