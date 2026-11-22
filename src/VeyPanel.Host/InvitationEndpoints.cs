using System.Net;
using System.Text.Json;

namespace VeyPanel.Host;

internal sealed class InvitationEndpoints(InvitationRegistry registry, string? lan)
{
    private readonly SemaphoreSlim slots = new(8, 8);
    private const string Owner = "/api/v1/devices/invitations";
    private const string Public = "/api/v1/enroll";

    internal static bool IsPublic(HttpContext c) =>
        HttpMethods.IsPost(c.Request.Method) && (c.Request.Path == Public + "/claim" || c.Request.Path == Public + "/finish");

    internal bool Allowed(HttpContext c)
    {
        if (lan is null || !c.Request.IsHttps || c.Connection.LocalPort != 47861
            || !IPAddress.TryParse(lan, out var ip) || !ip.Equals(c.Connection.LocalIpAddress)
            || c.Request.Host.Value != $"{lan}:47861" || c.Request.QueryString.HasValue)
            return false;
        var origins = c.Request.Headers.Origin;
        return origins.Count == 0 || (origins.Count == 1 && origins[0] == $"https://{lan}:47861");
    }

    internal void Map(WebApplication app)
    {
        app.MapGet(Owner, () => Results.Json(registry.List(DateTimeOffset.UtcNow)));
        app.MapPost(Owner, (Delegate)(Func<HttpContext, Task<IResult>>)CreateAsync);
        app.MapPost(Owner + "/{id:guid}/approve", (Delegate)(Func<HttpContext, Guid, Task<IResult>>)ApproveAsync);
        app.MapDelete(Owner + "/{id:guid}", (Guid id) => registry.Cancel(id) ? Results.NoContent() : Results.NotFound());
        app.MapPost(Public + "/claim", (Delegate)(Func<HttpContext, Task<IResult>>)(c => RedeemAsync(c, false)));
        app.MapPost(Public + "/finish", (Delegate)(Func<HttpContext, Task<IResult>>)(c => RedeemAsync(c, true)));
    }

    private Task<IResult> CreateAsync(HttpContext context) => ReadAsync(context, root =>
    {
        if (lan is null) return Results.Conflict();
        var name = Field(root, "name");
        if (!DeviceRegistry.ValidName(name)) return Results.BadRequest();
        var issued = registry.Create(name!, DateTimeOffset.UtcNow);
        if (issued is null) return Results.Conflict();
        var url = $"https://{lan}:47861/enroll.html#id={issued.Invitation.Id}&secret={issued.Secret}";
        try
        {
            var qrPng = InvitationQr.Render(url);
            return Results.Json(new { issued.Invitation, Url = url, QrPng = qrPng }, statusCode: 201);
        }
        catch (Exception)
        {
            registry.Cancel(issued.Invitation.Id);
            return Results.StatusCode(500);
        }
    });

    private Task<IResult> ApproveAsync(HttpContext context, Guid id) => ReadAsync(context, root =>
        registry.Approve(id, Field(root, "code") ?? "", DateTimeOffset.UtcNow) ? Results.NoContent() : Results.Conflict());

    private Task<IResult> RedeemAsync(HttpContext context, bool finish) => ReadAsync(context, root =>
    {
        if (!Allowed(context)) return Results.StatusCode(403);
        if (!Guid.TryParseExact(Field(root, "id"), "D", out var id) || Field(root, "secret") is not { Length: 64 } secret)
            return Results.BadRequest();
        if (!finish)
        {
            var claim = registry.Claim(id, secret, DateTimeOffset.UtcNow);
            return claim is null ? Results.NotFound() : Results.Json(claim);
        }
        var result = registry.Finish(id, secret, DateTimeOffset.UtcNow);
        return result.State switch
        {
            "issued" => Results.Json(result.Device, statusCode: 201),
            "pending" => Results.StatusCode(202),
            "capacity" => Results.Conflict(),
            _ => Results.NotFound()
        };
    });

    private async Task<IResult> ReadAsync(HttpContext context, Func<JsonElement, IResult> action)
    {
        if (context.Request.ContentLength is not (>= 1 and <= 1024)
            || !context.Request.HasJsonContentType()) return Results.BadRequest();
        if (!slots.Wait(0)) return Results.StatusCode(503);
        using var deadline = CancellationTokenSource.CreateLinkedTokenSource(context.RequestAborted);
        deadline.CancelAfter(TimeSpan.FromSeconds(5));
        try
        {
            using var json = await JsonDocument.ParseAsync(context.Request.Body,
                new JsonDocumentOptions { MaxDepth = 4 }, deadline.Token);
            return json.RootElement.ValueKind == JsonValueKind.Object ? action(json.RootElement) : Results.BadRequest();
        }
        catch (JsonException) { return Results.BadRequest(); }
        catch (OperationCanceledException) { return Results.StatusCode(408); }
        finally { slots.Release(); }
    }

    private static string? Field(JsonElement root, string key) =>
        root.TryGetProperty(key, out var field) && field.ValueKind == JsonValueKind.String ? field.GetString() : null;
}
