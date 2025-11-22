using AdaptiveTesting.Domain.Interfaces;
using AdaptiveTesting.Infrastructure.Persistence;
using AdaptiveTesting.Infrastructure.Services;
using AdaptiveTesting.Web.Components; 
using Microsoft.EntityFrameworkCore;
using Radzen;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();

// 1. РЕЄСТРАЦІЯ КОНТРОЛЕРІВ
builder.Services.AddControllers(); 

builder.Services.AddRadzenComponents();

// Реєстрація DbContext
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("DefaultConnection")));

// Реєстрація ML Client
builder.Services.AddHttpClient<IMlService, PythonMlClient>();

builder.Services.AddScoped<TestEngineService>();
builder.Services.AddScoped<AnalyticsService>();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment()) {
    app.UseExceptionHandler("/Error", createScopeForErrors: true);
    app.UseHsts();
}

app.UseHttpsRedirection();
app.UseStaticFiles();
app.UseAntiforgery();

app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

// 2. МАПІНГ КОНТРОЛЕРІВ
app.MapControllers(); 

app.Run();