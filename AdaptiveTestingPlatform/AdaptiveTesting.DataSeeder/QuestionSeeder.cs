using AdaptiveTesting.Domain.Entities;
using AdaptiveTesting.Infrastructure.Persistence;
using Microsoft.EntityFrameworkCore;
using System.Net.Http.Json;
using System.Text.Json;

public class QuestionSeeder {
    private readonly AppDbContext _db;
    private const string CacheFile = "quiz_cache.json";

    public QuestionSeeder(AppDbContext db) => _db = db;

    public async Task SeedAsync() {
        Console.WriteLine("Seeding Questions...");
        var questions = await LoadOrFetchQuestions();
        await _db.Questions.ExecuteDeleteAsync();

        var dbQuestions = new List<Question>();

        foreach (var q in questions) {
            if (!q.correct_answers.Any(x => x.Value == "true")) continue;
            var (options, correctIndex) = ParseOptions(q);

            dbQuestions.Add(new Question {
                Id = Guid.NewGuid(),
                Text = q.question,
                Topic = MapTopic(q.tags.FirstOrDefault()?.name),
                Difficulty = q.difficulty switch { "Easy" => -1.5, "Hard" => 1.5, _ => 0.0 },
                OptionsJson = JsonSerializer.Serialize(options),
                CorrectOptionIndex = correctIndex
            });
        }
        for (int i = 0; i < 5; i++) {
            var anomaly = dbQuestions.First(x => x.Difficulty > 1);
            anomaly.Text = "[ANOMALY] " + anomaly.Text;
            anomaly.Difficulty = -2.0;
        }

        await _db.Questions.AddRangeAsync(dbQuestions);
        await _db.SaveChangesAsync();
        Console.WriteLine($"Added {dbQuestions.Count} new questions.");
    }

    private async Task<List<QuizApiQuestion>> LoadOrFetchQuestions() {
        var list = new List<QuizApiQuestion>();
        if (!File.Exists(CacheFile)) await File.WriteAllTextAsync(CacheFile, "[]");
        list = JsonSerializer.Deserialize<List<QuizApiQuestion>>(await File.ReadAllTextAsync(CacheFile)) ?? [];

        var stop = false;
        using var client = new HttpClient();
        client.DefaultRequestHeaders.Add("X-Api-Key", "y0yye4hILNxANZdhfVfObxMMkb4rchLuCfPCsXOC");
        while (!stop) {
            try {
                var url = "https://quizapi.io/api/v1/questions?limit=20";
                var newQ = await client.GetFromJsonAsync<List<QuizApiQuestion>>(url);
                if (newQ != null) {
                    list = list.Concat(newQ).DistinctBy(x => x.id).ToList();
                }
            } catch {
                stop = true;
                Console.WriteLine("API limit reached, using cache only."); 
            }
        }
        await File.WriteAllTextAsync(CacheFile, JsonSerializer.Serialize(list));
        Console.WriteLine($"Fetched {list.Count} questions");
        return list;
    }

    private string MapTopic(string? rawTag) {
        if (string.IsNullOrEmpty(rawTag)) return "General";

        var t = rawTag.ToLower();

        if (t.Contains("sql") || t.Contains("db") || t.Contains("mysql") || t.Contains("postgres")) return "Database";
        if (t.Contains("docker") || t.Contains("kube") || t.Contains("linux") || t.Contains("bash") || t.Contains("devops")) return "DevOps";
        if (t.Contains("html") || t.Contains("css") || t.Contains("js") || t.Contains("react") || t.Contains("vue") || t.Contains("frontend")) return "Frontend";
        if (t.Contains("php") || t.Contains("laravel") || t.Contains("wordpress")) return "Backend_PHP";
        if (t.Contains("c#") || t.Contains(".net") || t.Contains("java") || t.Contains("spring")) return "Backend_Enterprise";

        return "General";
    }

    private (List<string> Options, int CorrectIndex) ParseOptions(QuizApiQuestion q) {
        var opts = q.answers.Where(x => x.Value != null).Select(x => x.Value).ToList();
        var correctKey = q.correct_answers.First(x => x.Value == "true").Key.Replace("_correct", "");
        var correctVal = q.answers[correctKey];
        return (opts, opts.IndexOf(correctVal));
    }
}
