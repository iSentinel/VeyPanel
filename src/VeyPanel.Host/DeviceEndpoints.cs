using System.Text.Json;

namespace VeyPanel.Host;

internal static class DeviceEndpoints
{
    internal static void Map(WebApplication app, DeviceRegistry registry, string? lan)
    {
        app.MapGet("/api/v1/devices/status", () => Results.Json(new { Storage = registry.StorageStatus }));
        app.MapDelete("/api/v1/devices", () => { registry.RevokeAll(); return Results.NoContent(); });
        app.MapGet("/api/v1/devices", () => Results.Json(registry.List(DateTimeOffset.UtcNow)));
        // Force the route-handler overload; a RequestDelegate could discard the returned IResult.
        Func<HttpContext, Task<IResult>> issue = context => IssueAsync(context, registry, lan);
        app.MapPost("/api/v1/devices", (Delegate)issue);
        app.MapDelete("/api/v1/devices/{id:guid}", (Guid id) =>
            registry.Revoke(id) ? Results.NoContent() : Results.NotFound());
    }

    private static async Task<IResult> IssueAsync(HttpContext context, DeviceRegistry registry, string? lan)
    {
        if (context.Request.ContentLength is not (>= 1 and <= 1024)
            || !context.Request.HasJsonContentType()) return Results.BadRequest();
        try
        {
            using var body = await JsonDocument.ParseAsync(context.Request.Body,
                new JsonDocumentOptions { MaxDepth = 4 }, context.RequestAborted);
            if (body.RootElement.ValueKind != JsonValueKind.Object
                || !body.RootElement.TryGetProperty("name", out var field)
                || field.ValueKind != JsonValueKind.String || !DeviceRegistry.ValidName(field.GetString()))
                return Results.BadRequest();
            var issued = registry.Issue(field.GetString()!, DateTimeOffset.UtcNow);
            if (issued is null) return Results.StatusCode(409);
            var url = lan is null ? null : $"https://{lan}:47861/#token={issued.Token}";
            return Results.Json(new { issued.Device, issued.Token, DashboardUrl = url }, statusCode: 201);
        }
        catch (JsonException) { return Results.BadRequest(); }
    }
}
