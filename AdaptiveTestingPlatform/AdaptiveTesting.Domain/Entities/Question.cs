namespace AdaptiveTesting.Domain.Entities;

public class Question {
    public Guid Id { get; set; }
    public string Text { get; set; } = string.Empty;
    public string Topic { get; set; } = "General";
    public double Difficulty { get; set; }
    public string OptionsJson { get; set; } = "[]";
    public int CorrectOptionIndex { get; set; }
}