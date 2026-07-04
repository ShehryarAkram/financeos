"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";

type Mode = "phone" | "email" | "otp";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("phone");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [isRegister, setIsRegister] = useState(false);
  const [orgName, setOrgName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // ── Phone + Password ──────────────────────────────────────────────
  const handlePhone = async () => {
    if (!phone || !password) { setError("Phone and password required"); return; }
    setLoading(true); setError("");
    try {
      if (isRegister) {
        if (!orgName) { setError("Business name required"); setLoading(false); return; }
        const res = await fetch(`${API}/api/auth/register`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ phone, password, full_name: orgName, org_name: orgName }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Registration failed");
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("org_id", data.org_id);
        localStorage.setItem("dukandaar_mode", data.dukandaar_mode);
        localStorage.setItem("phone", phone);
        localStorage.setItem("org_name", orgName);
      } else {
        const res = await fetch(`${API}/api/auth/login`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ phone, password }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Login failed");
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("org_id", data.org_id);
        localStorage.setItem("dukandaar_mode", data.dukandaar_mode);
        localStorage.setItem("phone", phone);
        localStorage.setItem("org_name", data.org_name || "");
      }
      router.push("/dashboard");
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  // ── Email + Password ──────────────────────────────────────────────
  const handleEmail = async () => {
    if (!email || !password) { setError("Email and password required"); return; }
    setLoading(true); setError("");
    try {
      if (isRegister) {
        const { error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
        setSuccess("Check your email to confirm your account.");
        setLoading(false); return;
      } else {
        const { data, error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        localStorage.setItem("token", data.session?.access_token || "");
        router.push("/dashboard");
      }
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  // ── WhatsApp OTP ──────────────────────────────────────────────────
  const handleSendOTP = async () => {
    if (!phone) { setError("Phone number required"); return; }
    setLoading(true); setError("");
    try {
      const formatted = phone.startsWith("+") ? phone : `+92${phone.replace(/^0/, "")}`;
      const { error } = await supabase.auth.signInWithOtp({ phone: formatted });
      if (error) throw error;
      setOtpSent(true);
      setSuccess(`OTP sent to ${formatted} via WhatsApp/SMS`);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const handleVerifyOTP = async () => {
    if (!otp) { setError("Enter the OTP code"); return; }
    setLoading(true); setError("");
    try {
      const formatted = phone.startsWith("+") ? phone : `+92${phone.replace(/^0/, "")}`;
      const { data, error } = await supabase.auth.verifyOtp({
        phone: formatted, token: otp, type: "sms",
      });
      if (error) throw error;
      localStorage.setItem("token", data.session?.access_token || "");
      router.push("/dashboard");
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  // ── Google OAuth ──────────────────────────────────────────────────
  const handleGoogle = async () => {
    setLoading(true);
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/dashboard` },
    });
    if (error) { setError(error.message); setLoading(false); }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4 py-8">
      <div className="w-full max-w-md">

        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 bg-green-600 rounded-2xl flex items-center justify-center text-white text-2xl font-bold mx-auto mb-4">F</div>
          <h1 className="text-2xl font-bold text-gray-900">FinanceOS</h1>
          <p className="text-sm text-gray-500 mt-1">Pakistan ka apna hisaab kitab</p>
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">

          {/* Mode tabs */}
          <div className="flex gap-1 bg-gray-100 rounded-lg p-1 mb-6">
            {(["phone", "email", "otp"] as Mode[]).map(m => (
              <button key={m} onClick={() => { setMode(m); setError(""); setSuccess(""); setOtpSent(false); }}
                className={`flex-1 text-xs font-medium py-1.5 rounded-md transition-colors ${
                  mode === m ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
                }`}>
                {m === "phone" ? "📱 Phone" : m === "email" ? "✉️ Email" : "💬 OTP"}
              </button>
            ))}
          </div>

          {/* Errors / success */}
          {error && <div className="bg-red-50 text-red-600 text-sm px-4 py-2.5 rounded-lg mb-4">{error}</div>}
          {success && <div className="bg-green-50 text-green-700 text-sm px-4 py-2.5 rounded-lg mb-4">{success}</div>}

          {/* ── PHONE MODE ── */}
          {mode === "phone" && (
            <div className="space-y-3">
              {isRegister && (
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">Business Name *</label>
                  <input className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                    placeholder="Ahmed General Store" value={orgName} onChange={e => setOrgName(e.target.value)} />
                </div>
              )}
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Phone Number *</label>
                <input className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                  placeholder="03001234567" value={phone} onChange={e => setPhone(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && handlePhone()} />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Password *</label>
                <input type="password" className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                  placeholder="••••••••" value={password} onChange={e => setPassword(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && handlePhone()} />
              </div>
              <button onClick={handlePhone} disabled={loading}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2.5 rounded-lg transition-colors disabled:opacity-50 text-sm">
                {loading ? "Please wait..." : isRegister ? "Create Account" : "Sign In"}
              </button>
              <p className="text-center text-xs text-gray-500">
                {isRegister ? "Already have an account?" : "New to FinanceOS?"}{" "}
                <button onClick={() => { setIsRegister(!isRegister); setError(""); }}
                  className="text-green-600 font-medium hover:text-green-700">
                  {isRegister ? "Sign in" : "Create account"}
                </button>
              </p>
            </div>
          )}

          {/* ── EMAIL MODE ── */}
          {mode === "email" && (
            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Email *</label>
                <input type="email" className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                  placeholder="you@example.com" value={email} onChange={e => setEmail(e.target.value)} />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Password *</label>
                <input type="password" className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                  placeholder="••••••••" value={password} onChange={e => setPassword(e.target.value)} />
              </div>
              <button onClick={handleEmail} disabled={loading}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2.5 rounded-lg transition-colors disabled:opacity-50 text-sm">
                {loading ? "Please wait..." : isRegister ? "Create Account" : "Sign In with Email"}
              </button>
              <p className="text-center text-xs text-gray-500">
                {isRegister ? "Already registered?" : "No account?"}{" "}
                <button onClick={() => { setIsRegister(!isRegister); setError(""); }}
                  className="text-green-600 font-medium">
                  {isRegister ? "Sign in" : "Register"}
                </button>
              </p>
            </div>
          )}

          {/* ── OTP MODE ── */}
          {mode === "otp" && (
            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Phone Number</label>
                <input className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                  placeholder="03001234567" value={phone} onChange={e => setPhone(e.target.value)}
                  disabled={otpSent} />
              </div>
              {!otpSent ? (
                <button onClick={handleSendOTP} disabled={loading}
                  className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2.5 rounded-lg transition-colors disabled:opacity-50 text-sm">
                  {loading ? "Sending..." : "Send OTP via SMS"}
                </button>
              ) : (
                <>
                  <div>
                    <label className="text-xs text-gray-500 mb-1 block">Enter 6-digit OTP</label>
                    <input className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 text-center text-lg tracking-widest"
                      placeholder="000000" maxLength={6} value={otp} onChange={e => setOtp(e.target.value)} />
                  </div>
                  <button onClick={handleVerifyOTP} disabled={loading}
                    className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2.5 rounded-lg transition-colors disabled:opacity-50 text-sm">
                    {loading ? "Verifying..." : "Verify & Sign In"}
                  </button>
                  <button onClick={() => { setOtpSent(false); setOtp(""); setSuccess(""); }}
                    className="w-full text-gray-500 text-xs hover:text-gray-700">
                    ← Change number
                  </button>
                </>
              )}
            </div>
          )}

          {/* Divider */}
          <div className="flex items-center gap-3 my-5">
            <div className="flex-1 h-px bg-gray-100"></div>
            <span className="text-xs text-gray-400">or continue with</span>
            <div className="flex-1 h-px bg-gray-100"></div>
          </div>

          {/* Social buttons */}
          <button onClick={() => { setMode("otp"); setError(""); }}
              className="w-full flex items-center justify-center gap-2 border border-gray-200 rounded-lg py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors">
              💬 Continue with WhatsApp OTP
            </button>

        </div>

        <p className="text-center text-xs text-gray-400 mt-6">
          Pakistan ka pehla AI-powered finance tool 🇵🇰
        </p>
      </div>
    </div>
  );
}
