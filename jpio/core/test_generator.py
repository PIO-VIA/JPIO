from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .models import TestPlan

def _make_env() -> Environment:
    """
    Creates the Jinja2 environment pointing to jpio/templates/.
    """
    templates_dir = Path(__file__).parent.parent / "templates"
    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(
            enabled_extensions=("j2",),
            default_for_string=True,
        ),
        trim_blocks=True,
        lstrip_blocks=True,
    )

def generate_tests(test_plan: TestPlan) -> dict[str, str]:
    """
    Renders templates for each TestClass in the plan.
    Returns: { filepath: java_content }
    """
    env = _make_env()
    output = {}

    for tc in test_plan.test_classes:
        # 1. Choose template
        template_map = {
            "SERVICE_IMPL": "tests/service_test.java.j2",
            "CONTROLLER":   "tests/controller_test.java.j2",
            "REPOSITORY":   "tests/repository_test.java.j2",
            "MAPPER":       "tests/mapper_test.java.j2"
        }
        
        template_name = template_map.get(tc.test_type)
        if not template_name:
            continue

        template = env.get_template(template_name)

        # 2. Render
        content = template.render(tc=tc, base_package=tc.base_package)

        # 3. Path
        # src/test/java/com/pio/ecommerce/service/ProductServiceImplTest.java
        package_path = tc.package_name.replace(".", "/")
        dest_path = f"src/test/java/{package_path}/{tc.test_class_name}.java"

        output[dest_path] = content

    return output
