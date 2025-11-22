namespace AdaptiveTesting.Domain.Entities;

public class User {
    public Guid Id { get; set; }
    public string FullName { get; set; } = string.Empty;
    public string Role { get; set; } = "Student";
    public int? ClusterLabel { get; set; }
    public List<UserTopicState> TopicStates { get; set; } = new();
}