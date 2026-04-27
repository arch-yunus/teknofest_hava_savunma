import { describe, expect, it } from "vitest";
import { appRouter } from "./routers";
import type { TrpcContext } from "./_core/context";

type AuthenticatedUser = NonNullable<TrpcContext["user"]>;

function createTestContext(): TrpcContext {
  const user: AuthenticatedUser = {
    id: 1,
    openId: "test-user",
    email: "test@example.com",
    name: "Test User",
    loginMethod: "test",
    role: "user",
    createdAt: new Date(),
    updatedAt: new Date(),
    lastSignedIn: new Date(),
  };

  const ctx: TrpcContext = {
    user,
    req: {
      protocol: "https",
      headers: {},
    } as TrpcContext["req"],
    res: {
      clearCookie: () => {},
    } as TrpcContext["res"],
  };

  return ctx;
}

describe("simulation router", () => {
  describe("getLatestData", () => {
    it("returns initial simulation data structure", async () => {
      const ctx = createTestContext();
      const caller = appRouter.createCaller(ctx);

      const result = await caller.simulation.getLatestData();

      expect(result).toBeDefined();
      expect(result.timestamp).toBeGreaterThan(0);
      expect(result.targets).toBeInstanceOf(Array);
      expect(result.system_health).toBeDefined();
      expect(result.system_health.battery).toBe(100);
      expect(result.system_health.cpu).toBe(15);
      expect(result.system_health.snr).toBe(95);
      expect(result.system_health.temperature).toBe(42);
      expect(result.system_health.interceptorsReady).toBe(12);
      expect(result.system_health.muhimmat).toBe(50);
      expect(result.current_stage).toBe(1);
      expect(result.auto_fire_enabled).toBe(true);
      expect(result.radar_emission).toBe(true);
      expect(result.weather).toBe("CLEAR");
    });
  });

  describe("sendCommand", () => {
    it("accepts valid stage commands", async () => {
      const ctx = createTestContext();
      const caller = appRouter.createCaller(ctx);

      const stageCommands = ["set_stage_1", "set_stage_2", "set_stage_3"] as const;

      for (const action of stageCommands) {
        const result = await caller.simulation.sendCommand({
          action: action as any,
        });

        expect(result).toEqual({ success: true });
      }
    });

    it("accepts valid control commands", async () => {
      const ctx = createTestContext();
      const caller = appRouter.createCaller(ctx);

      const controlCommands = [
        "toggle_auto_fire",
        "toggle_radar_emission",
        "toggle_weather",
        "manual_fire",
        "force_swarm",
        "trigger_emp",
        "trigger_estop",
        "release_estop",
      ] as const;

      for (const action of controlCommands) {
        const result = await caller.simulation.sendCommand({
          action: action as any,
          target_id: action === "manual_fire" ? "T001" : undefined,
        });

        expect(result).toEqual({ success: true });
      }
    });

    it("handles manual fire with target_id", async () => {
      const ctx = createTestContext();
      const caller = appRouter.createCaller(ctx);

      const result = await caller.simulation.sendCommand({
        action: "manual_fire",
        target_id: "T001",
      });

      expect(result).toEqual({ success: true });
    });

    it("handles commands without target_id", async () => {
      const ctx = createTestContext();
      const caller = appRouter.createCaller(ctx);

      const result = await caller.simulation.sendCommand({
        action: "force_swarm",
      });

      expect(result).toEqual({ success: true });
    });
  });

  describe("TEKNOFEST 2026 compliance", () => {
    it("supports all three operational stages", async () => {
      const ctx = createTestContext();
      const caller = appRouter.createCaller(ctx);

      // Test Stage 1: Stationary targets
      const stage1 = await caller.simulation.sendCommand({
        action: "set_stage_1",
      });
      expect(stage1.success).toBe(true);

      // Test Stage 2: Swarm attack
      const stage2 = await caller.simulation.sendCommand({
        action: "set_stage_2",
      });
      expect(stage2.success).toBe(true);

      // Test Stage 3: Layered defense
      const stage3 = await caller.simulation.sendCommand({
        action: "set_stage_3",
      });
      expect(stage3.success).toBe(true);
    });

    it("supports auto-fire toggle for autonomous engagement", async () => {
      const ctx = createTestContext();
      const caller = appRouter.createCaller(ctx);

      const toggleResult = await caller.simulation.sendCommand({
        action: "toggle_auto_fire",
      });

      expect(toggleResult.success).toBe(true);
    });

    it("supports radar emission control for stealth", async () => {
      const ctx = createTestContext();
      const caller = appRouter.createCaller(ctx);

      const toggleResult = await caller.simulation.sendCommand({
        action: "toggle_radar_emission",
      });

      expect(toggleResult.success).toBe(true);
    });

    it("supports weather simulation for environmental challenges", async () => {
      const ctx = createTestContext();
      const caller = appRouter.createCaller(ctx);

      const weatherResult = await caller.simulation.sendCommand({
        action: "toggle_weather",
      });

      expect(weatherResult.success).toBe(true);
    });

    it("supports emergency stop for safety", async () => {
      const ctx = createTestContext();
      const caller = appRouter.createCaller(ctx);

      const estopResult = await caller.simulation.sendCommand({
        action: "trigger_estop",
      });

      expect(estopResult.success).toBe(true);
    });
  });
});
