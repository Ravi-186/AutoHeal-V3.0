import streamlit as st
import streamlit.components.v1 as components
import os

_component_path = os.path.join(os.path.dirname(__file__), "assets", "attack_path_component")
_attack_path_3d = components.declare_component("attack_path_3d", path=_component_path)

def render_attack_path_3d(devices, path, timeline_step, verified_devices=None, height=600):
    """
    Renders the 3D Attack Path component.
    Returns the value sent back from JavaScript (e.g., node click events).
    """
    return _attack_path_3d(
        devices=devices,
        path=path,
        timelineStep=timeline_step,
        verified_devices=verified_devices or [],
        height=height,
        default=None
    )
