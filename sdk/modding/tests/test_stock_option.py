"""Expose the feature-owned tests through the existing portable SDK discovery."""
import importlib.util
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "examples/stock-option/test_source.py"
spec = importlib.util.spec_from_file_location("stock_option_feature_source_tests", path)
feature = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feature)
StockOptionSourceTests = feature.StockOptionSourceTests

trace_path = path.with_name("test_trace.py")
trace_spec = importlib.util.spec_from_file_location("stock_option_feature_trace_tests", trace_path)
trace_feature = importlib.util.module_from_spec(trace_spec)
trace_spec.loader.exec_module(trace_feature)
StockOptionTraceTests = trace_feature.StockOptionTraceTests
