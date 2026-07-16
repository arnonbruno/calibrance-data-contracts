"""
Canonical enums for the Calibrance data foundry contracts.

These enums are used across the data-foundry ingestion pipeline, the SaaS
backend, and downstream consumers to ensure a consistent vocabulary for
source types, processing states, signal channels, and augmentation classes.
"""

from __future__ import annotations

from enum import Enum


class SourceType(str, Enum):
    """Identifies the upstream origin / adapter family for a dataset."""

    UCI_ROBOT_FAILURES = "uci_robot_failures"
    AURSAD = "aursad"
    VORAUS_AD = "voraus_ad"
    ROBOMIMIC = "robomimic"
    OPEN_X = "open_x"
    DROID = "droid"
    GENERIC_CSV = "generic_csv"
    GENERIC_HDF5 = "generic_hdf5"
    GENERIC_PARQUET = "generic_parquet"
    ROSBAG = "rosbag"
    MCAP = "mcap"
    CUSTOM_API = "custom_api"
    UNKNOWN = "unknown"


class HydrationLevel(str, Enum):
    """
    How much of a source has been materialised locally.

    H0_METADATA         – only metadata (catalog row) has been ingested.
    H1_MANIFEST          – a version manifest + rights policy exist.
    H2_STRATIFIED_SAMPLE – a representative stratified sample is stored.
    H3_FULL              – the entire source is downloaded/normalised.
    """

    H0_METADATA = "h0_metadata"
    H1_MANIFEST = "h1_manifest"
    H2_STRATIFIED_SAMPLE = "h2_stratified_sample"
    H3_FULL = "h3_full"


class SourceState(str, Enum):
    """
    Lifecycle state machine for a dataset source.

    Transition order (happy path):
        DISCOVERED → METADATA_INGESTED → RIGHTS_REVIEW_PENDING →
        APPROVED_METADATA_ONLY → APPROVED_DOWNLOAD →
        NORMALIZED → QUALITY_APPROVED → TRAIN_ELIGIBLE → ACTIVE

    Side branches:
        - QUARANTINED  (transient / blocking issue under investigation)
        - WITHDRAWN     (upstream removed the dataset)
        - SUPERSEDED    (replaced by a newer version)
        - REJECTED      (rights / quality gate failed permanently)
    """

    DISCOVERED = "discovered"
    METADATA_INGESTED = "metadata_ingested"
    RIGHTS_REVIEW_PENDING = "rights_review_pending"
    APPROVED_METADATA_ONLY = "approved_metadata_only"
    APPROVED_DOWNLOAD = "approved_download"
    QUARANTINED = "quarantined"
    NORMALIZED = "normalized"
    QUALITY_APPROVED = "quality_approved"
    TRAIN_ELIGIBLE = "train_eligible"
    ACTIVE = "active"
    WITHDRAWN = "withdrawn"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"


class SignalChannel(str, Enum):
    """
    Canonical signal channel identifiers.

    Each value is a stable, machine-readable channel name.  The data foundry
    normalises heterogeneous source signals into these channels so that
    downstream consumers (augmentation, training, evaluation) have a single
    vocabulary.
    """

    # Joint-level signals (per-DOF arrays)
    JOINT_POSITION_RAD = "joint_position_rad"
    JOINT_VELOCITY_RAD_S = "joint_velocity_rad_s"
    JOINT_EFFORT_NM = "joint_effort_nm"
    JOINT_CURRENT_A = "joint_current_a"
    JOINT_TEMPERATURE_C = "joint_temperature_c"
    JOINT_TORQUE_NM = "joint_torque_nm"

    # TCP / end-effector signals
    TCP_POSE = "tcp_pose"
    TCP_WRENCH = "tcp_wrench"
    TCP_VELOCITY = "tcp_velocity"

    # Gripper / end-effector actuator
    GRIPPER_POSITION = "gripper_position"
    GRIPPER_FORCE = "gripper_force"

    # Cartesian / pose channels
    CARTESIAN_POSITION = "cartesian_position"
    CARTESIAN_ORIENTATION = "cartesian_orientation"

    # Robot state / controller
    ROBOT_MODE = "robot_mode"
    SAFETY_STOP = "safety_stop"
    CONTROLLER_STATE = "controller_state"

    # Time
    TIMESTAMP_NS = "timestamp_ns"

    # Action / command channels
    ACTION_POSITION = "action_position"
    ACTION_VELOCITY = "action_velocity"
    ACTION_TORQUE = "action_torque"

    # Environment / external
    ENV_TEMPERATURE_C = "env_temperature_c"
    ENV_HUMIDITY = "env_humidity"

    # Generic catch-all for uncategorised channels
    MISC = "misc"


class AugmentationClass(str, Enum):
    """
    High-level taxonomy for augmentation strategies.

    LABEL_PRESERVING         – transform does not change the label.
    LABEL_TRANSFORMING        – transform may change the label (e.g. time warp).
    COUNTERFACTUAL_PHYSICS    – physics-based counterfactual generation.
    SIMULATED                 – synthetic data from a simulator.
    VISUAL_SEMANTIC           – visual / semantic perturbations.
    GENERATIVE_TIME_SERIES    – generative model producing new time-series.
    """

    LABEL_PRESERVING = "label_preserving"
    LABEL_TRANSFORMING = "label_transforming"
    COUNTERFACTUAL_PHYSICS = "counterfactual_physics"
    SIMULATED = "simulated"
    VISUAL_SEMANTIC = "visual_semantic"
    GENERATIVE_TIME_SERIES = "generative_time_series"


class TransformClass(str, Enum):
    """
    Concrete transform identifiers used in the augmentation ontology.

    These are the individual operations that can be applied; each maps to one
    :class:`AugmentationClass`.
    """

    JITTER = "jitter"
    SCALING = "scaling"
    MAGNITUDE_WARP = "magnitude_warp"
    TIME_WARP = "time_warp"
    PERMUTATION = "permutation"
    WINDOW_WARP = "window_warp"
    NOISE_INJECTION = "noise_injection"
    MASKING = "masking"
    MIXUP = "mixup"
    CUTMIX = "cutmix"
    ROTATION = "rotation"
    TRANSLATION = "translation"
    CROP = "crop"
    FLIP = "flip"
    COLOR_JITTER = "color_jitter"
    GAUSSIAN_BLUR = "gaussian_blur"
    DOMAIN_SHIFT = "domain_shift"
    PHYSICS_COUNTERFACTUAL = "physics_counterfactual"
    SIM_INJECTION = "sim_injection"
    GAN_GENERATION = "gan_generation"
    DIFFUSION_GENERATION = "diffusion_generation"
    TIME_SERIES_FORECAST = "time_series_forecast"


class Modality(str, Enum):
    """Media modality for :class:`MediaStreamRef`."""

    VIDEO = "video"
    AUDIO = "audio"
    DEPTH = "depth"
    RGBD = "rgbd"
    POINTCLOUD = "pointcloud"
    THERMAL = "thermal"
    OTHER = "other"


class LabelType(str, Enum):
    """Type of an :class:`EventLabel`."""

    OBSERVED_EVENT = "observed_event"
    ROOT_CAUSE = "root_cause"
    INTERVENTION = "intervention"
    OUTCOME = "outcome"


class LabelSource(str, Enum):
    """Who/what produced an :class:`EventLabel`."""

    HUMAN_EXPERT = "human_expert"
    HUMAN_CROWD = "human_crowd"
    ALGORITHM = "algorithm"
    MAINTENANCE_LOG = "maintenance_log"
    SENSOR_FUSION = "sensor_fusion"
    GROUND_TRUTH = "ground_truth"


class GroundTruthMethod(str, Enum):
    """How the ground-truth status of a label was established."""

    MANUAL_INSPECTION = "manual_inspection"
    MAINTENANCE_RECORD = "maintenance_record"
    CONTROLLED_FAULT_INJECTION = "controlled_fault_injection"
    SIMULATOR = "simulator"
    STATISTICAL_BASELINE = "statistical_baseline"
    UNKNOWN = "unknown"
