import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import ForgotPasswordPage from "./page";

describe("ForgotPasswordPage", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          message: "If an account exists for that email, a reset link has been sent",
        }),
      }),
    );
  });

  afterEach(() => vi.unstubAllGlobals());

  it("shows the privacy-safe confirmation after requesting a reset link", async () => {
    render(<ForgotPasswordPage />);

    fireEvent.change(screen.getByPlaceholderText("Email Address"), {
      target: { value: "ada@example.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: /send reset link/i }));

    await act(async () => {
      await Promise.resolve();
    });

    expect(screen.getByRole("status")).toHaveTextContent(
      "If an account exists",
    );
  });
});
