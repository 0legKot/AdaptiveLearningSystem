using AdaptiveTesting.Infrastructure.Persistence;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.Text;

namespace AdaptiveTesting.Web.Controllers;

[Route("api/export")]
[ApiController]
public class ExportController : ControllerBase {
    private readonly AppDbContext _db;

    public ExportController(AppDbContext db) {
        _db = db;
    }

    [HttpGet("results")]
    public async Task<IActionResult> DownloadCsv() {
        var sessions = await _db.TestSessions
            .Include(s => s.User)
            .Include(s => s.Answers)
            .OrderByDescending(s => s.StartedAt)
            .ToListAsync();

        var sb = new StringBuilder();
        // CSV Header
        sb.AppendLine("Student Name,Date,Questions Answered,Score %,Is Suspicious,ML Cluster");

        foreach (var s in sessions) {
            var score = s.Answers.Any() ? (double)s.Answers.Count(a => a.IsCorrect) / s.Answers.Count * 100 : 0;
            var cluster = s.User.ClusterLabel switch { 0 => "Cheater", 1 => "Junior", 2 => "Senior", _ => "Unknown" };

            sb.AppendLine($"{s.User.FullName},{s.StartedAt},{s.Answers.Count},{score:F1},{s.IsSuspicious},{cluster}");
        }

        var bytes = Encoding.UTF8.GetBytes(sb.ToString());
        return File(bytes, "text/csv", $"Report_{DateTime.Now:yyyyMMdd}.csv");
    }
}