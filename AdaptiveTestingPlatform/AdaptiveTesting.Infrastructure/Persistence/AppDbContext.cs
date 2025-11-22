using AdaptiveTesting.Domain.Entities;
using Microsoft.EntityFrameworkCore;

namespace AdaptiveTesting.Infrastructure.Persistence;

public class AppDbContext : DbContext {
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    public DbSet<User> Users { get; set; }
    public DbSet<Question> Questions { get; set; }
    public DbSet<TestSession> TestSessions { get; set; }
    public DbSet<AnswerLog> AnswerLogs { get; set; }
    public DbSet<UserTopicState> UserTopicStates { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder) {
        modelBuilder.Entity<AnswerLog>()
            .HasIndex(a => a.SessionId);

        modelBuilder.Entity<User>()
            .HasIndex(u => u.ClusterLabel);
    }
}