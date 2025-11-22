using AdaptiveTesting.Domain.Entities;

namespace AdaptiveTesting.Infrastructure.Services;

public class UserSessionService {
    public User? CurrentUser { get; private set; }
    public bool IsTeacher { get; private set; }

    public event Action? OnChange;

    public void LoginStudent(User user) {
        CurrentUser = user;
        IsTeacher = false;
        NotifyStateChanged();
    }

    public void LoginAsTeacher() {
        CurrentUser = new User { FullName = "Professor Dumbledore", Role = "Teacher" };
        IsTeacher = true;
        NotifyStateChanged();
    }

    public void Logout() {
        CurrentUser = null;
        IsTeacher = false;
        NotifyStateChanged();
    }

    private void NotifyStateChanged() => OnChange?.Invoke();
}