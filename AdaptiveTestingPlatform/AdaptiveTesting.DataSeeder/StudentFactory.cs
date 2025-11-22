public static class StudentFactory {
    public static List<Archetype> GetArchetypes() => new()
    {

        new Archetype("Enterprise Dev", new() { {"Backend_Enterprise", 2.5}, {"Database", 1.5}, {"DevOps", 0.5}, {"Frontend", -1.0}, {"Backend_PHP", -1.0} }),

        new Archetype("PHP Fullstack", new() { {"Backend_PHP", 2.5}, {"Frontend", 2.0}, {"Database", 1.0}, {"Backend_Enterprise", -2.0}, {"DevOps", -1.0} }),

        new Archetype("DevOps Engineer", new() { {"DevOps", 2.5}, {"Database", 0.0}, {"Backend_Enterprise", -0.5}, {"Frontend", -2.0}, {"Backend_PHP", -0.5} }),

        new Archetype("Cheater", new(), IsCheater: true),

        new Archetype("Junior Intern", new() { {"Frontend", 0.0}, {"Backend_PHP", -0.5}, {"Database", -0.5}, {"DevOps", -1.5} })
    };
}