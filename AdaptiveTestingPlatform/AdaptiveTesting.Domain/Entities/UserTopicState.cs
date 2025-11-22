namespace AdaptiveTesting.Domain.Entities;

public class UserTopicState {
    public Guid Id { get; set; }
    public Guid UserId { get; set; }
    public string TopicName { get; set; } = string.Empty;
    public double AbilityTheta { get; set; } = 0.0;
    public DateTime LastUpdated { get; set; }
}