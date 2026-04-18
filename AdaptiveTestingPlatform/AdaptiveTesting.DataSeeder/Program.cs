using AdaptiveTesting.Infrastructure.Persistence;
using Microsoft.EntityFrameworkCore;

Console.OutputEncoding = System.Text.Encoding.UTF8;
var optionsBuilder = new DbContextOptionsBuilder<AppDbContext>();
optionsBuilder.UseSqlServer("Server=(localdb)\\mssqllocaldb;Database=AdaptiveTestingDb;Trusted_Connection=True;MultipleActiveResultSets=true");

using var db = new AppDbContext(optionsBuilder.Options);

await db.Database.EnsureCreatedAsync();

var reCreateQ = true;
var simulate = true;

Console.WriteLine("STARTING SEEDING...");
if (reCreateQ) {
    var questionSeeder = new QuestionSeeder(db);
    await questionSeeder.SeedAsync();
    Console.WriteLine("Question seeding finished");
}
if (reCreateQ || simulate) {
    var simulator = new ExamSimulator(db);
    await simulator.RunSimulationAsync(studentCount: 100);
    Console.WriteLine("Exam seeding finished");
}

Console.WriteLine("SEEDING FINISHED! ");
