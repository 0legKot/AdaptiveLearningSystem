namespace AdaptiveTesting.Domain.Entities;

public class AnswerLog {
    public Guid Id { get; set; }
    public Guid SessionId { get; set; }
    public Guid QuestionId { get; set; }
    public bool IsCorrect { get; set; }
    public int TimeSpentMs { get; set; }
    public int FocusLostEvents { get; set; }

    public TestSession? Session { get; set; }
    public Question? Question { get; set; }
}