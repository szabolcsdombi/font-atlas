from typing import List, Tuple

def load_font(
    size: Tuple[int, int],
    fonts: List[str],
    font_sizes: List[int],
    code_points: List[int],
    oversampling: int = 1,
    padding: int = 1,
) -> Tuple[bytes, bytes]: ...
