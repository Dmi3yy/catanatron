"""Optional Gymnasium environment registration."""

try:
    from gymnasium.envs.registration import register
except ModuleNotFoundError:  # pragma: no cover - gymnasium optional
    register = None

if register:
    register(
        id="catanatron/Catanatron-v0",
        entry_point="catanatron.gym.envs:CatanatronEnv",
    )
