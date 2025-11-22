namespace AdaptiveTesting.DataSeeder;

public class QuizApiQuestion {
    public int id { get; set; }
    public string question { get; set; }
    public Dictionary<string, string> answers { get; set; }
    public Dictionary<string, string> correct_answers { get; set; }
    public string difficulty { get; set; }
    public List<Tag> tags { get; set; }
}

public class Tag {
    public string name { get; set; }
}