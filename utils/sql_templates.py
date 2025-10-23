"""
SQL Template Manager

Provides access to pre-optimized SQL query templates for common analytics patterns.
Uses templates from the semantic layer's query patterns configuration.

Usage:
    from utils.sql_templates import get_template, suggest_template, list_templates

    # Get a specific template
    sql = get_template("top_performing_content", user_id="abc123", days=7)

    # Find matching template for a user query
    template_name = suggest_template("show me my top posts")
    if template_name:
        sql = get_template(template_name, user_id="abc123")
"""

from typing import Dict, List, Optional
from utils.semantic_layer import semantic_layer
import logging
import re

logger = logging.getLogger(__name__)


def get_template(template_name: str, **params) -> Optional[str]:
    """
    Get a SQL template filled with parameters.

    Args:
        template_name: Name of the template pattern
        **params: Parameters to fill in the template (e.g., user_id, days, limit)

    Returns:
        SQL query string with parameters filled in, or None if template not found

    Example:
        >>> sql = get_template("top_performing_content", user_id="user123", days=30, limit=10)
        >>> "user123" in sql
        True
    """
    return semantic_layer.get_pattern_template(template_name, **params)


def suggest_template(user_query: str) -> Optional[str]:
    """
    Suggest the best template for a user's natural language query.

    Uses the semantic layer's query pattern matching to find appropriate templates.

    Args:
        user_query: Natural language query from user

    Returns:
        Template name if a good match is found, None otherwise

    Example:
        >>> suggest_template("show me my best posts")
        'top_performing_content'
    """
    return semantic_layer.match_query_pattern(user_query)


def list_templates(category: Optional[str] = None) -> List[Dict[str, any]]:
    """
    List all available SQL templates.

    Args:
        category: Optional filter by category (e.g., "social_media", "ecommerce")

    Returns:
        List of template metadata dictionaries

    Example:
        >>> templates = list_templates(category="social_media")
        >>> len(templates) > 0
        True
    """
    all_patterns = semantic_layer.query_patterns

    templates = []
    for pattern_name, pattern_def in all_patterns.items():
        # Filter by category if specified
        if category and pattern_def.get('category') != category:
            continue

        template_info = {
            "name": pattern_name,
            "display_name": pattern_def.get('name', pattern_name),
            "category": pattern_def.get('category', 'general'),
            "description": pattern_def.get('description', ''),
            "use_cases": pattern_def.get('use_cases', []),
            "parameters": pattern_def.get('parameters', {}),
            "metrics_calculated": pattern_def.get('metrics_calculated', [])
        }
        templates.append(template_info)

    return templates


def get_template_metadata(template_name: str) -> Optional[Dict]:
    """
    Get metadata about a specific template.

    Args:
        template_name: Name of the template pattern

    Returns:
        Dictionary with template metadata, or None if not found

    Example:
        >>> meta = get_template_metadata("top_performing_content")
        >>> meta['category']
        'social_media'
    """
    pattern = semantic_layer.get_query_pattern(template_name)
    if not pattern:
        return None

    return {
        "name": template_name,
        "display_name": pattern.get('name', template_name),
        "category": pattern.get('category', 'general'),
        "description": pattern.get('description', ''),
        "use_cases": pattern.get('use_cases', []),
        "parameters": pattern.get('parameters', {}),
        "metrics_calculated": pattern.get('metrics_calculated', []),
        "has_template": 'template' in pattern
    }


def format_template_suggestion(template_name: str, user_query: str) -> str:
    """
    Format a template suggestion message for the user.

    Args:
        template_name: Name of the suggested template
        user_query: User's original query

    Returns:
        Formatted suggestion message

    Example:
        >>> msg = format_template_suggestion("top_performing_content", "show best posts")
        >>> "optimized" in msg.lower()
        True
    """
    metadata = get_template_metadata(template_name)
    if not metadata:
        return ""

    message_parts = []
    message_parts.append(f"💡 **Optimization Suggestion**: I found a pre-optimized query template for this request:")
    message_parts.append(f"\n**Template**: {metadata['display_name']}")
    message_parts.append(f"**Description**: {metadata['description']}")

    if metadata['metrics_calculated']:
        metrics_str = ", ".join(metadata['metrics_calculated'])
        message_parts.append(f"**Calculates**: {metrics_str}")

    message_parts.append("\nThis template is optimized for performance and accuracy.")

    return "\n".join(message_parts)


def validate_template_parameters(template_name: str, **params) -> Dict[str, any]:
    """
    Validate that required parameters are provided for a template.

    Args:
        template_name: Name of the template
        **params: Parameters being passed to the template

    Returns:
        Dictionary with:
        - is_valid: bool
        - missing: list of missing required parameters
        - invalid: list of parameters with wrong types
        - defaults_applied: dict of default values used

    Example:
        >>> result = validate_template_parameters("top_performing_content", user_id="user123")
        >>> result['is_valid']
        True
        >>> 'days' in result['defaults_applied']
        True
    """
    pattern = semantic_layer.get_query_pattern(template_name)
    if not pattern:
        return {
            "is_valid": False,
            "error": f"Template '{template_name}' not found",
            "missing": [],
            "invalid": [],
            "defaults_applied": {}
        }

    param_defs = pattern.get('parameters', {})
    missing = []
    invalid = []
    defaults_applied = {}

    # Check required parameters
    for param_name, param_def in param_defs.items():
        is_required = param_def.get('required', False)
        param_type = param_def.get('type', 'string')
        default_value = param_def.get('default')

        if param_name not in params:
            if is_required:
                missing.append(param_name)
            elif default_value is not None:
                defaults_applied[param_name] = default_value
        else:
            # Validate type (basic check)
            value = params[param_name]
            expected_type = {'string': str, 'int': int, 'float': float, 'bool': bool}.get(param_type, str)

            if not isinstance(value, expected_type):
                invalid.append({
                    "parameter": param_name,
                    "expected_type": param_type,
                    "actual_type": type(value).__name__
                })

    is_valid = len(missing) == 0 and len(invalid) == 0

    return {
        "is_valid": is_valid,
        "missing": missing,
        "invalid": invalid,
        "defaults_applied": defaults_applied
    }


def get_template_with_validation(template_name: str, **params) -> Dict[str, any]:
    """
    Get template with parameter validation and helpful error messages.

    Args:
        template_name: Name of the template
        **params: Parameters to fill in

    Returns:
        Dictionary with:
        - success: bool
        - sql: Generated SQL if successful
        - error: Error message if failed
        - validation: Validation result details

    Example:
        >>> result = get_template_with_validation("top_performing_content", user_id="user123")
        >>> result['success']
        True
    """
    # Validate parameters
    validation = validate_template_parameters(template_name, **params)

    if not validation['is_valid']:
        error_parts = []
        if validation.get('error'):
            error_parts.append(validation['error'])
        if validation['missing']:
            error_parts.append(f"Missing required parameters: {', '.join(validation['missing'])}")
        if validation['invalid']:
            invalid_details = [f"{inv['parameter']} (expected {inv['expected_type']})" for inv in validation['invalid']]
            error_parts.append(f"Invalid parameter types: {', '.join(invalid_details)}")

        return {
            "success": False,
            "sql": None,
            "error": "; ".join(error_parts),
            "validation": validation
        }

    # Apply defaults
    final_params = {**validation['defaults_applied'], **params}

    # Get template
    sql = get_template(template_name, **final_params)

    if sql is None:
        return {
            "success": False,
            "sql": None,
            "error": f"Failed to generate SQL from template '{template_name}'",
            "validation": validation
        }

    return {
        "success": True,
        "sql": sql,
        "error": None,
        "validation": validation
    }


def search_templates_by_keyword(keyword: str) -> List[str]:
    """
    Search for templates by keyword in name, description, or use cases.

    Args:
        keyword: Search keyword

    Returns:
        List of matching template names

    Example:
        >>> templates = search_templates_by_keyword("engagement")
        >>> len(templates) > 0
        True
    """
    keyword_lower = keyword.lower()
    matching_templates = []

    for pattern_name, pattern_def in semantic_layer.query_patterns.items():
        # Check name
        if keyword_lower in pattern_name.lower():
            matching_templates.append(pattern_name)
            continue

        # Check display name
        if keyword_lower in pattern_def.get('name', '').lower():
            matching_templates.append(pattern_name)
            continue

        # Check description
        if keyword_lower in pattern_def.get('description', '').lower():
            matching_templates.append(pattern_name)
            continue

        # Check use cases
        use_cases = pattern_def.get('use_cases', [])
        if any(keyword_lower in uc.lower() for uc in use_cases):
            matching_templates.append(pattern_name)
            continue

        # Check metrics calculated
        metrics = pattern_def.get('metrics_calculated', [])
        if any(keyword_lower in metric.lower() for metric in metrics):
            matching_templates.append(pattern_name)

    return matching_templates
