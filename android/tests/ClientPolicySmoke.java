package com.veypanel.client;

import java.time.Instant;

public final class ClientPolicySmoke {
    public static void main(String[] args) {
        String token = "A".repeat(64);
        ReaderSession session = ReaderSession.parse("https://192.168.1.10:47861/#token=" + token);
        check(session.endpoint.toString().equals("https://192.168.1.10:47861/api/v1/telemetry"), "Fixed endpoint; no query secret");
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
