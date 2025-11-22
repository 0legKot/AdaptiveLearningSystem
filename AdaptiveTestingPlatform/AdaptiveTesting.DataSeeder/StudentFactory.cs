public static class StudentFactory {
    public static List<Archetype> GetArchetypes() => new()
    {
        // 1. Enterprise Backend (C#, DB +, JS -)
        new Archetype("Enterprise Dev", new() { {"Backend_Enterprise", 2.5}, {"Database", 1.5}, {"DevOps", 0.5}, {"Frontend", -1.0}, {"Backend_PHP", -1.0} }),
        
        // 2. PHP Fullstack (PHP, Frontend +, C# -)
        new Archetype("PHP Fullstack", new() { {"Backend_PHP", 2.5}, {"Frontend", 2.0}, {"Database", 1.0}, {"Backend_Enterprise", -2.0}, {"DevOps", -1.0} }),
        
        // 3. DevOps (Linux, Docker +, Code -)
        new Archetype("DevOps Engineer", new() { {"DevOps", 2.5}, {"Database", 0.0}, {"Backend_Enterprise", -0.5}, {"Frontend", -2.0}, {"Backend_PHP", -0.5} }),
        
        // 4. Cheater (100% accuracy, fast time)
        new Archetype("Cheater", new(), IsCheater: true),

        // 5. Junior (Weak everywhere)
        new Archetype("Junior Intern", new() { {"Frontend", 0.0}, {"Backend_PHP", -0.5}, {"Database", -0.5}, {"DevOps", -1.5} })
    };
}
