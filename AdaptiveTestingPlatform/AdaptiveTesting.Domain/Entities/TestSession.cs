namespace AdaptiveTesting.Domain.Entities;

public class TestSession {
    public Guid Id { get; set; }
    public Guid UserId { get; set; }
    public DateTime StartedAt { get; set; }
    public DateTime? FinishedAt { get; set; }
    public bool IsSuspicious { get; set; }

    public User? User { get; set; }
    public List<AnswerLog> Answers { get; set; } = new();
}