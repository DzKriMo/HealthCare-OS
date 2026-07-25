"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { api } from "@/lib/api/client";

interface MfaSetupProps {
  onComplete: () => void;
  onSkip: () => void;
}

type Step = "loading" | "qr" | "confirm" | "done";

export function MfaSetup({ onComplete, onSkip }: MfaSetupProps) {
  const [step, setStep] = useState<Step>("loading");
  const [secret, setSecret] = useState("");
  const [qrUri, setQrUri] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const setup = useCallback(async () => {
    setError("");
    try {
      const result = await api.post<{ secret: string; qr_uri: string }>("/auth/mfa/setup/");
      setSecret(result.secret);
      setQrUri(result.qr_uri);
      setStep("qr");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to initialize MFA setup");
      setStep("qr");
    }
  }, []);

  useEffect(() => {
    setup();
  }, [setup]);

  const handleConfirm = async () => {
    if (code.trim().length < 6) return;
    setSubmitting(true);
    setError("");
    try {
      await api.post("/auth/mfa/confirm/", { code: code.trim() });
      setStep("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed");
    } finally {
      setSubmitting(false);
    }
  };

  if (step === "loading") {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Set up two-factor authentication</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Set up two-factor authentication</CardTitle>
        <CardDescription>
          {step === "qr" && "Scan the QR code with your authenticator app, then enter the verification code."}
          {step === "confirm" && "Enter the 6-digit code from your authenticator app."}
          {step === "done" && "Two-factor authentication has been enabled."}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {step === "qr" && qrUri && (
          <>
            <div className="flex justify-center">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={qrUri}
                alt="MFA QR Code"
                className="h-48 w-48 rounded-md border"
              />
            </div>
            <div className="space-y-1 text-center">
              <p className="text-xs text-muted-foreground">
                Or enter this secret manually:
              </p>
              <p className="select-all rounded bg-muted px-3 py-1 font-mono text-sm">
                {secret}
              </p>
            </div>
            <div className="flex justify-center">
              <Button
                variant="outline"
                onClick={() => setStep("confirm")}
              >
                I have scanned the code
              </Button>
            </div>
          </>
        )}

        {step === "confirm" && (
          <div className="space-y-2">
            <Label htmlFor="mfa-code">Verification code</Label>
            <Input
              id="mfa-code"
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              maxLength={6}
              placeholder="000000"
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
              autoFocus
            />
          </div>
        )}

        {step === "done" && (
          <div className="flex justify-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-100 text-green-600">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </div>
        )}
      </CardContent>
      <CardFooter className="justify-end gap-2">
        {step === "qr" && (
          <Button variant="ghost" onClick={onSkip}>
            Skip
          </Button>
        )}
        {step === "confirm" && (
          <>
            <Button variant="ghost" onClick={() => setStep("qr")}>
              Back
            </Button>
            <Button
              onClick={handleConfirm}
              disabled={code.trim().length < 6 || submitting}
            >
              {submitting ? "Verifying..." : "Confirm"}
            </Button>
          </>
        )}
        {step === "done" && (
          <Button onClick={onComplete}>
            Continue
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}
