using AdaptiveTesting.DataSeeder;
using AdaptiveTesting.Domain.Entities;
using AdaptiveTesting.Infrastructure.Persistence;
using Bogus;
using Microsoft.EntityFrameworkCore;
using System;
using System.Net.Http.Json;
using System.Text.Json;

// Налаштування контексту (LocalDB)
var optionsBuilder = new DbContextOptionsBuilder<AppDbContext>();
optionsBuilder.UseSqlServer("Server=(localdb)\\mssqllocaldb;Database=AdaptiveTestingDb;Trusted_Connection=True;MultipleActiveResultSets=true");

using var db = new AppDbContext(optionsBuilder.Options);
await db.Database.EnsureCreatedAsync();

await SeedQuestionsAsync(db);
await SeedStudentHistoryAsync(db);

Console.WriteLine("SEEDING COMPLETED SUCCESSFULLY!");


static async Task SeedQuestionsAsync(AppDbContext db) {
    const string CacheFile = "quiz_cache.json";
    var cachedQuestions = new List<QuizApiQuestion>();

    // 1. Спроба завантажити локальний кеш
    if (File.Exists(CacheFile)) {
        Console.WriteLine("Loading questions from local cache file...");
        try {
            var json = await File.ReadAllTextAsync(CacheFile);
            cachedQuestions = JsonSerializer.Deserialize<List<QuizApiQuestion>>(json) ?? new();
            Console.WriteLine($"Loaded {cachedQuestions.Count} questions from cache.");
        } catch { Console.WriteLine("Cache file corrupted, starting fresh."); }
    }

    // 2. Спроба отримати НОВІ дані з API
    Console.WriteLine("Fetching FRESH questions from QuizAPI...");
    using var client = new HttpClient();

    client.DefaultRequestHeaders.Add("X-Api-Key", "ogx5YdVabzOaQIGA6yshBl6wR8qMz1jMfTCN7KtV");

    var url = "https://quizapi.io/api/v1/questions?limit=20";

    var newQuestions = new List<QuizApiQuestion>();
    try {
        newQuestions = await client.GetFromJsonAsync<List<QuizApiQuestion>>(url) ?? new();
        Console.WriteLine($"Fetched {newQuestions.Count} new questions from API.");
    } catch (Exception ex) {
        Console.WriteLine($"API Request failed (Quota limit?): {ex.Message}. Using only cache.");
    }

    // 3. Об'єднання та збереження (Merge & Save)
    // Додаємо нові до старих, фільтруємо дублікати по ID
    var allQuestions = cachedQuestions
        .Concat(newQuestions)
        .DistinctBy(q => q.id)
        .ToList();

    if (newQuestions.Any()) {
        Console.WriteLine($"Updating cache file. Total unique questions: {allQuestions.Count}");
        var options = new JsonSerializerOptions { WriteIndented = true };
        await File.WriteAllTextAsync(CacheFile, JsonSerializer.Serialize(allQuestions, options));
    }

    // 4. Запис у БД (Тільки тих, яких ще немає в базі)
    // Перевіряємо, які ID вже є в базі, щоб не вставляти дублікати при кожному запуску
    var existingIds = await db.Questions.Select(q => q.Text).ToListAsync(); // Використовуємо Text як унікальний ключ, якщо ID генеруються нові

    var dbQuestions = new List<Question>();

    foreach (var q in allQuestions) {
        // Якщо питання з таким текстом вже є в базі - пропускаємо
        if (existingIds.Contains(q.question)) continue;

        var correctKey = q.correct_answers.FirstOrDefault(x => x.Value == "true").Key;
        if (correctKey == null) continue;

        var cleanKey = correctKey.Replace("_correct", "");
        var optionsList = q.answers.Where(x => x.Value != null).Select(x => x.Value).ToList();
        var correctText = q.answers[cleanKey];
        var correctIndex = optionsList.IndexOf(correctText);

        double diff = q.difficulty switch { "Easy" => -1.5, "Hard" => 1.5, _ => 0.0 };
        string topic = q.tags?.FirstOrDefault()?.name ?? "General";

        dbQuestions.Add(new Question {
            Id = Guid.NewGuid(),
            Text = q.question, // Використовуємо це для перевірки на дублікати
            Topic = topic,
            Difficulty = diff,
            OptionsJson = JsonSerializer.Serialize(optionsList),
            CorrectOptionIndex = correctIndex
        });
    }

    if (dbQuestions.Any()) {
        await db.Questions.AddRangeAsync(dbQuestions);
        await db.SaveChangesAsync();
        Console.WriteLine($"Saved {dbQuestions.Count} NEW questions to Database.");
    } else {
        Console.WriteLine("Database is up to date. No new questions added.");
    }
}

static async Task SeedStudentHistoryAsync(AppDbContext db) {
    if (db.Users.Any()) return;

    var questions = await db.Questions.ToListAsync();
    var faker = new Faker();
    var random = new Random();
    var users = new List<User>();
    var logs = new List<AnswerLog>();
    var sessions = new List<TestSession>();

    Console.WriteLine("Simulating 50 students...");

    for (int i = 0; i < 50; i++) {
        // 0 - Cheater, 1 - Junior, 2 - Senior
        int type = random.Next(0, 3);

        var user = new User {
            Id = Guid.NewGuid(),
            FullName = faker.Name.FullName(),
            Role = "Student",
            // Ми заздалегідь знаємо лейбл (Ground Truth), ML має це вгадати
            ClusterLabel = type
        };
        users.Add(user);

        var session = new TestSession {
            Id = Guid.NewGuid(),
            UserId = user.Id,
            StartedAt = DateTime.Now.AddDays(-random.Next(1, 10)),
            FinishedAt = DateTime.Now,
            IsSuspicious = type == 0
        };
        sessions.Add(session);

        // Кожен проходить 10 випадкових питань
        var testQs = questions.OrderBy(x => random.Next()).Take(10);

        foreach (var q in testQs) {
            bool isCorrect = false;
            int time = 0;
            int focusLost = 0;

            switch (type) {
                case 0: // Cheater: Швидко, правильно, втрачає фокус
                    isCorrect = true;
                    time = random.Next(1000, 4000);
                    focusLost = random.Next(1, 5);
                    break;
                case 1: // Junior: Довго, помиляється на складних
                    time = random.Next(15000, 40000);
                    // Sigmoid probability
                    double prob = 1.0 / (1.0 + Math.Exp(-(-1.0 - q.Difficulty)));
                    isCorrect = random.NextDouble() < prob;
                    break;
                case 2: // Senior: Середньо, правильно
                    time = random.Next(5000, 20000);
                    double probS = 1.0 / (1.0 + Math.Exp(-(1.5 - q.Difficulty)));
                    isCorrect = random.NextDouble() < probS;
                    break;
            }

            logs.Add(new AnswerLog {
                Id = Guid.NewGuid(),
                SessionId = session.Id,
                QuestionId = q.Id,
                IsCorrect = isCorrect,
                TimeSpentMs = time,
                FocusLostEvents = focusLost
            });
        }
    }

    await db.Users.AddRangeAsync(users);
    await db.TestSessions.AddRangeAsync(sessions);
    await db.AnswerLogs.AddRangeAsync(logs);
    await db.SaveChangesAsync();
}