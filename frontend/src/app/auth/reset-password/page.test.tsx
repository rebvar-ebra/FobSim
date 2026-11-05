import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import ResetPasswordPage from "./page";

const replace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
}));

describe("ResetPasswordPage", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    replace.mockReset();
    window.history.replaceState(
      null,
      "",
      "/auth/reset-password#token=signed-reset-token",
    );
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ message: "Password updated successfully" }),
      }),
    );
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("confirms the reset before returning to login", async () => {
    await act(async () => {
      render(<ResetPasswordPage />);
      await Promise.resolve();
    });

    expect(window.location.hash).toBe("");

    fireEvent.change(screen.getByPlaceholderText("New Password"), {
      target: { value: "new-password" },
    });
    fireEvent.change(screen.getByPlaceholderText("Confirm New Password"), {
      target: { value: "new-password" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save new password/i }));

    await act(async () => {
      await Promise.resolve();
    });

    expect(screen.getByRole("status")).toHaveTextContent(
      "Password updated successfully",
    );
    expect(replace).not.toHaveBeenCalled();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1500);
    });

    expect(replace).toHaveBeenCalledWith("/auth/login");
  });

  it("shows an invalid-link state before the form can be used", async () => {
    window.history.replaceState(null, "", "/auth/reset-password");

    await act(async () => {
      render(<ResetPasswordPage />);
      await Promise.resolve();
    });

    expect(screen.getByRole("alert")).toHaveTextContent(
      "This reset link is missing or invalid",
    );
    expect(
      screen.getByRole("link", { name: /request another link/i }),
    ).toHaveAttribute("href", "/auth/forgot-password");
    expect(
      screen.queryByRole("button", { name: /save new password/i }),
    ).not.toBeInTheDocument();
  });
});
