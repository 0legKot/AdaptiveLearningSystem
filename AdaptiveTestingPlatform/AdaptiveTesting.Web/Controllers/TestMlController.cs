using AdaptiveTesting.Domain.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace AdaptiveTesting.Web.Controllers;

[Route("api/[controller]")]
[ApiController]
public class TestMlController : ControllerBase {
    private readonly IMlService _mlService;

    public TestMlController(IMlService mlService) {
        _mlService = mlService;
    }

    [HttpGet("check")]
    public async Task<IActionResult> Check() {
        // Тестуємо BKT: Якщо студент знав на 0.5 і відповів правильно -> має стати більше
        var newTheta = await _mlService.PredictKnowledgeAsync(0.5, true);

        // Тестуємо Anti-Cheat: 1 секунда на відповідь -> має бути true (підозра)
        var isCheater = await _mlService.IsSuspiciousBehaviorAsync(1000, 5);

        return Ok(new {
            BKT_Result = newTheta,
            AntiCheat_Result = isCheater,
            Message = "Integration Works!"
        });
    }
}