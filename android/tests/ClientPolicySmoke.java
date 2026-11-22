package com.veypanel.client;

import java.time.Instant;

public final class ClientPolicySmoke {
    public static void main(String[] args) {
        String token = "A".repeat(64);
        ReaderSession session = ReaderSession.parse("https://192.168.1.10:47861/#token=" + token);
        check(session.endpoint.toString().equals("https://192.168.1.10:47861/api/v1/telemetry"), "Fixed endpoint; no query secret");
        check(session.websocketUrl().equals("wss://192.168.1.10:47861/api/v1/telemetry/ws"), "WSS fixed same-origin path, no token");
        for (String host : new String[] {"127.0.0.1", "8.8.8.8", "100.64.1.2", "192.168.01.2", "192.168.256.1", "172.32.0.1", "example.com"})
            reject("https://" + host + ":47861/#token=" + token);
        reject("http://192.168.1.10:47861/#token=" + token);
        reject("https://192.168.1.10:443/#token=" + token);
        reject("https://192.168.1.10:47861/?x=1#token=" + token);
        reject("https://192.168.1.10:47861/enroll.html#token=" + token);
        reject("https://192.168.1.10:47861/#token=bad");
        check(ReaderSession.privateIp("172.16.0.1") && ReaderSession.privateIp("172.31.1.2") && ReaderSession.privateIp("10.1.1.1"), "Private ranges");
        Instant now = Instant.parse("2026-11-22T12:00:00Z");
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
