package com.veypanel.client;

import java.time.Instant;

public final class ClientPolicySmoke {
    public static void main(String[] args) {
        String token = "A".repeat(64);
        ReaderSession session = ReaderSession.parse("https://192.168.1.10:47861/#token=" + token);
        check(session.endpoint.toString().equals("https://192.168.1.10:47861/api/v1/telemetry"), "Fixed endpoint; no query secret");
        check(session.sameAccess(ReaderSession.parse("https://192.168.1.10:47861/#token=" + token))
            && !session.sameAccess(null)
            && !session.sameAccess(ReaderSession.parse("https://192.168.1.11:47861/#token=" + token))
            && !session.sameAccess(ReaderSession.parse("https://192.168.1.10:47861/#token=" + "B".repeat(64))), "Saved access identity includes origin and token");
        check(session.websocketUrl().equals("wss://192.168.1.10:47861/api/v1/telemetry/ws"), "WSS fixed same-origin path, no token");
        for (String host : new String[] {"127.0.0.1", "8.8.8.8", "100.64.1.2", "192.168.01.2", "192.168.256.1", "172.32.0.1", "example.com"})
            reject("https://" + host + ":47861/#token=" + token);
        ReaderSession fixture = ReaderSession.fixture('A');
        check(fixture.endpoint.getHost().equals("127.0.0.1") && fixture.token.equals(token)
            && fixture.websocketUrl().equals("wss://127.0.0.1:47861/api/v1/telemetry/ws"), "Fixed instrumentation endpoint");
        boolean rejectedFixture = false;
        try { ReaderSession.fixture('X'); } catch (IllegalArgumentException ex) { rejectedFixture = true; }
        check(rejectedFixture, "Only synthetic fixture tokens allowed");
        reject("http://192.168.1.10:47861/#token=" + token);
        reject("https://192.168.1.10:443/#token=" + token);
        reject("https://192.168.1.10:47861/?x=1#token=" + token);
        reject("https://192.168.1.10:47861/enroll.html#token=" + token);
        reject("https://192.168.1.10:47861/#token=bad");
        check(ReaderSession.privateIp("172.16.0.1") && ReaderSession.privateIp("172.31.1.2") && ReaderSession.privateIp("10.1.1.1"), "Private ranges");
        Instant now = Instant.parse("2026-11-22T12:00:00Z");
        check(SampleRules.timestamp("2026-11-22T12:00:00+00:00").equals(now)
            && SampleRules.timestamp("2026-11-22T14:00:00.1234567+02:00").equals(now.plusNanos(123456700))
            && SampleRules.timestamp("2026-11-22T12:00:00Z").equals(now), "Windows offset timestamp normalization");
        boolean noOffset = false;
        try { SampleRules.timestamp("2026-11-22T12:00:00"); }
        catch (java.time.format.DateTimeParseException ex) { noOffset = true; }
        check(noOffset, "Offset required");
        check(SampleRules.fresh(now.minusSeconds(5), now) && !SampleRules.fresh(now.minusSeconds(6), now)
            && !SampleRules.fresh(now.plusSeconds(6), now), "Sample freshness");
        check(SampleRules.percent(0) == 0 && SampleRules.percent(100) == 100 && SampleRules.percent(null) == null
            && SampleRules.percent("0") == null && SampleRules.percent(Double.NaN) == null && SampleRules.percent(101) == null
            && SampleRules.nonnegative(-1) == null && SampleRules.nonnegative(1024) == 1024, "Null and numeric validation");
        String invite = "https://192.168.1.10:47861/enroll.html#id=11111111-2222-3333-4444-555555555555&secret=" + token;
        InvitationLink link = InvitationLink.parse(invite);
        check(link.endpoint(false).toString().equals("https://192.168.1.10:47861/api/v1/enroll/claim")
            && link.endpoint(true).toString().endsWith("/api/v1/enroll/finish")
            && link.reader(token).endpoint.equals(session.endpoint), "Invitation origin and fixed endpoints");
        for (String unsafe : new String[] {invite.replace("https:", "http:"), invite.replace("192.168.1.10", "8.8.8.8"),
            invite.replace("enroll.html", "other.html"), invite.replace("#id=", "?id="), invite + "&x=1"}) {
            boolean rejected = false;
            try { InvitationLink.parse(unsafe); } catch (IllegalArgumentException ex) { rejected = true; }
            check(rejected, "Unsafe invitation rejected");
        }
        SavedReader record = new SavedReader(session, now);
        check(SavedReader.decode(record.encode(), now).session.endpoint.equals(session.endpoint)
            && !record.validAt(now.minusSeconds(1)) && !record.validAt(now.plusSeconds(86400)), "Saved reader origin and bounded age");
        boolean expired = false;
        try { SavedReader.decode(record.encode(), now.plusSeconds(86400)); }
        catch (IllegalArgumentException ex) { expired = true; }
        check(expired, "Expired saved reader rejected");
        ConnectionDiagnostics diagnostics = new ConnectionDiagnostics();
        diagnostics.attempt(); diagnostics.fallback(); diagnostics.networkError(); diagnostics.fresh(false, 1000);
        String report = diagnostics.describe(4000);
        check(report.contains("REST") && report.contains("attempts: 1") && report.contains("Fallbacks: 1")
            && report.contains("errors: 1") && report.contains("samples: 1") && report.contains("3 s ago"), "Reconnect diagnostics");
        diagnostics.reset();
        check(diagnostics.describe(4000).contains("IDLE") && diagnostics.describe(4000).contains("N/A"), "Diagnostics reset");
        FrameHeaderSmoke.run();
        MessageReaderSmoke.run();
        UpgradeSmoke.run();
        TouchMathSmoke.run();
        LocalTouchProbeSmoke.run();
        System.out.println("PASS: native client policy fixtures");
    }
    private static void reject(String link) {
        try { ReaderSession.parse(link); } catch (IllegalArgumentException ex) { return; }
        throw new IllegalStateException("Unsafe link accepted");
    }
    private static void check(boolean ok, String label) {
        if (!ok) throw new IllegalStateException(label);
        System.out.println("PASS: " + label);
    }
}
