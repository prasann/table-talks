"""Templates for schema analyzer output formatting."""

from typing import Dict, List, Any, Callable

# Template definitions for different output types
TEMPLATES = {
    "table_list": {
        "title": "Database Tables ({total_count} total)",
        "columns": [
            {"name": "Table", "style": "cyan", "no_wrap": True},
            {"name": "Columns", "justify": "right", "style": "magenta"},
            {"name": "Rows", "justify": "right", "style": "green"},
            {"name": "Sample Columns", "style": "dim"}
        ],
        "row_mapper": lambda item: [
            item['name'], 
            str(item['columns']), 
            f"{item['rows']:,}" if isinstance(item['rows'], int) else str(item['rows']),
            item['sample_cols']
        ],
        "empty_message": "No tables found in the database",
        "empty_style": "yellow"
    },
    
    "schema_detail": {
        "panel": {
            "title": "Schema: {table_name}",
            "style": "blue"
        },
        "stats_format": "Rows: [green]{row_count:,}[/green] | Columns: [magenta]{col_count}[/magenta] | Size: [yellow]{size_mb:.1f} MB[/yellow]",
        "columns_table": {
            "title": "Columns",
            "header_style": "bold magenta",
            "columns": [
                {"name": "Column", "style": "cyan"},
                {"name": "Type", "style": "yellow"},
                {"name": "Nullable", "justify": "center", "style": "dim"},
                {"name": "Constraints", "style": "green"}
            ],
            "row_mapper": lambda col: [
                col['name'],
                str(col['type']),
                "✓" if col['nullable'] else "✗",
                col.get('constraints_str', '')
            ]
        },
        "sections": {
            "primary_keys": {
                "title": "[bold green]Primary Keys:[/bold green]",
                "format": "{keys}"
            },
            "foreign_keys": {
                "title": "[bold blue]Foreign Keys:[/bold blue]",
                "format": "  • {constrained_cols} → {referred_table}({referred_cols})"
            },
            "indexes": {
                "title": "[bold yellow]Indexes:[/bold yellow]",
                "format": "  • {idx_name}: {idx_cols}{unique_str}"
            }
        }
    },
    
    "database_summary": {
        "panel": {
            "title": "Database Summary",
            "style": "blue"
        },
        "stats": [
            "Database: [cyan]{database_path}[/cyan]",
            "Total tables: [green]{total_tables}[/green]",
            "Total rows: [yellow]{total_rows:,}[/yellow]",
            "Total columns: [magenta]{total_columns}[/magenta]"
        ],
        "tables_breakdown": {
            "title": "Tables Breakdown",
            "columns": [
                {"name": "Table", "style": "cyan"},
                {"name": "Rows", "justify": "right", "style": "green"},
                {"name": "Columns", "justify": "right", "style": "magenta"},
                {"name": "Data Types", "style": "dim"}
            ],
            "row_mapper": lambda table_info: [
                table_info['name'],
                f"{table_info['row_count']:,}",
                str(table_info['column_count']),
                table_info['types_str']
            ]
        }
    },
    
    "data_quality": {
        "panel_good": {
            "title": "Data Quality: {score:.1f}% (Excellent)",
            "style": "green"
        },
        "panel_fair": {
            "title": "Data Quality: {score:.1f}% (Good)",
            "style": "yellow"
        },
        "panel_poor": {
            "title": "Data Quality: {score:.1f}% (Needs Attention)",
            "style": "red"
        },
        "stats": [
            "Tables analyzed: [cyan]{total_tables}[/cyan]",
            "Issues found: [red]{issues_count}[/red]" if "{issues_count}" != "0" else "Issues found: [green]0[/green] ✨"
        ],
        "issues_section": {
            "title": "[bold red]Top Issues:[/bold red]",
            "format": "  {index}. {issue}",
            "more_format": "  ... and {remaining} more issues"
        },
        "quality_table": {
            "title": "Quality by Table",
            "columns": [
                {"name": "Table", "style": "cyan"},
                {"name": "Quality Score", "justify": "right"},
                {"name": "Status", "justify": "center"}
            ],
            "row_mapper": lambda table: [
                table['name'],
                f"{table['score']:.1f}%" if table.get('score') is not None else "—",
                table['status']
            ]
        }
    },
    
    "column_search": {
        "title": "Search Results for '{search_term}' ({count} found)",
        "columns": [
            {"name": "Table", "style": "cyan"},
            {"name": "Column", "style": "bright_cyan"},
            {"name": "Type", "style": "yellow"},
            {"name": "Nullable", "justify": "center", "style": "dim"}
        ],
        "row_mapper": lambda match: [
            match['table'],
            match['column'],
            str(match['type']),
            "✓" if match['nullable'] else "✗"
        ],
        "empty_message": "No columns found containing '{search_term}'",
        "empty_style": "yellow"
    },
    
    "column_analysis": {
        "panel": {
            "title": "Column '{column_name}' Analysis",
            "subtitle": "Found in {count} tables"
        },
        "consistency_good": "[green]Type Consistency: GOOD[/green] - All tables use the same type",
        "consistency_bad": "[yellow]Type Consistency: INCONSISTENT[/yellow] - {type_count} different types found",
        "columns_table": {
            "columns": [
                {"name": "Table", "style": "cyan"},
                {"name": "Data Type", "style": "magenta"},
                {"name": "Nullable", "justify": "center"},
                {"name": "Primary Key", "justify": "center"},
                {"name": "Default", "style": "dim"},
                {"name": "Rows", "justify": "right", "style": "dim"}
            ],
            "row_mapper": lambda info: [
                info['table_name'],
                info['type_str'],
                info['nullable_str'],
                info['pk_str'],
                info['default_str'],
                f"{info['table_rows']:,}"
            ]
        },
        "summary": [
            "Summary: {instances} instances, {total_rows:,} total rows across all tables",
            "Primary key in {pk_count} table(s)" if "{pk_count}" != "0" else None,
            "Nullable in {nullable_count} table(s)" if "{nullable_count}" != "0" else None
        ]
    },
    
    "common_columns": {
        "panel": {
            "title": "Common Columns",
            "subtitle": "{count} columns found in multiple tables"
        },
        "main_table": {
            "columns": [
                {"name": "Column", "style": "cyan"},
                {"name": "Tables", "justify": "right", "style": "dim"},
                {"name": "Type Consistency", "justify": "center"},
                {"name": "Tables Found In", "style": "dim"}
            ],
            "row_mapper": lambda col: [
                col['name'],
                str(col['table_count']),
                col['consistency_str'],
                col['tables_str']
            ]
        },
        "inconsistencies_table": {
            "title": "Type Inconsistencies",
            "columns": [
                {"name": "Column", "style": "cyan"},
                {"name": "Table", "style": "yellow"},
                {"name": "Data Type", "style": "magenta"},
                {"name": "Nullable", "justify": "center"}
            ]
        },
        "recommendations": [
            "Consider standardizing types for: [yellow]{inconsistent_types}[/yellow]",
            "Potential join columns: [green]{potential_joins}[/green]",
            "High-frequency columns (consider as schema standards): [cyan]{high_frequency}[/cyan]"
        ],
        "empty_message": "No columns found that appear in multiple tables",
        "empty_style": "yellow"
    },
    
    "type_mismatches": {
        "panel": {
            "title": "Type Mismatches Found",
            "subtitle": "{count} columns with inconsistent types",
            "style": "red"
        },
        "table": {
            "columns": [
                {"name": "Column", "style": "cyan"},
                {"name": "Type Count", "justify": "center", "style": "magenta"},
                {"name": "Table Count", "justify": "center", "style": "yellow"},
                {"name": "Details", "style": "dim"}
            ],
            "row_mapper": lambda mismatch: [
                mismatch['column'],
                str(mismatch['type_count']),
                str(mismatch['table_count']),
                mismatch['details']
            ]
        },
        "recommendations": [
            "Review data loading processes for type consistency",
            "Consider explicit type casting during data import",
            "Standardize column types across related tables",
            "[red]High priority columns to fix:[/red] [yellow]{high_impact}[/yellow]"
        ],
        "summary": "Summary: {mismatch_count} columns with {variant_count} total type variants",
        "success_message": "[green]No type mismatches found! All common columns have consistent types.[/green] ✨",
        "empty_style": "green"
    },
    
    "schema_comparison": {
        "panel": {
            "title": "Schema Comparison",
            "subtitle": "{file1} vs {file2}"
        },
        "stats_table": {
            "columns": [
                {"name": "Table", "style": "cyan"},
                {"name": "Rows", "justify": "right", "style": "green"},
                {"name": "Columns", "justify": "right", "style": "magenta"}
            ]
        },
        "summary": [
            "Common columns: [green]{common_count}[/green]",
            "Only in {file1}: [yellow]{only_in_1}[/yellow]",
            "Only in {file2}: [blue]{only_in_2}[/blue]"
        ],
        "common_table": {
            "title": "Common Columns ({count})",
            "columns": [
                {"name": "Column", "style": "cyan"},
                {"name": "{file1} Type", "style": "magenta"},
                {"name": "{file2} Type", "style": "magenta"},
                {"name": "Match", "justify": "center"}
            ]
        },
        "unique_table": {
            "columns": [
                {"name": "Column", "style": "cyan"},
                {"name": "Type", "style": "magenta"}
            ]
        },
        "compatibility": {
            "identical": "[green]Schemas are identical[/green] ✨",
            "same_cols_diff_types": "[yellow]Same columns but some type differences[/yellow]",
            "no_common": "[red]No common columns - tables are completely different[/red]",
            "high": "[green]High compatibility ({percentage:.1f}%)[/green]",
            "moderate": "[yellow]Moderate compatibility ({percentage:.1f}%)[/yellow]",
            "low": "[red]Low compatibility ({percentage:.1f}%)[/red]"
        }
    },
    
    "data_quality_basic": {
        "panel_good": {
            "title": "Data Quality (Basic): {score:.1f}% (Good)",
            "style": "green"
        },
        "panel_fair": {
            "title": "Data Quality (Basic): {score:.1f}% (Fair)",
            "style": "yellow"
        },
        "panel_poor": {
            "title": "Data Quality (Basic): {score:.1f}% (Poor)",
            "style": "red"
        },
        "quality_table": {
            "columns": [
                {"name": "Table", "style": "cyan"},
                {"name": "Rows", "justify": "right", "style": "dim"},
                {"name": "Columns", "justify": "right", "style": "dim"},
                {"name": "Quality Score", "justify": "right"},
                {"name": "Issues", "justify": "right"},
                {"name": "Status", "justify": "center"}
            ],
            "row_mapper": lambda table: [
                table['name'],
                f"{table['row_count']:,}",
                str(table['column_count']),
                f"{table['quality_score']:.1f}%",
                str(table['issue_count']),
                table['status']
            ]
        },
        "sample_issues": {
            "title": "[bold red]Sample Issues:[/bold red]",
            "format": "  • {table_name}: {issue}"
        }
    }
}

# Message templates for common scenarios
MESSAGES = {
    "errors": {
        "sql_unavailable": "[red]SQLAlchemy not available - {operation}[/red]",
        "table_not_found": "[red]Table '{table}' not found[/red]",
        "available_tables": "[dim]Available tables: {tables}[/dim]",
        "general_error": "[red]Error {operation}: {error}[/red]",
        "search_term_required": "[red]Please provide a search term[/red]",
        "column_name_required": "[red]Please provide a column name[/red]",
        "both_tables_required": "[red]Please provide both table names[/red]"
    },
    "warnings": {
        "insufficient_tables": "[yellow]Need at least 2 tables to {operation}[/yellow]",
        "gx_fallback": "[dim]Great Expectations analysis failed, falling back to basic analysis[/dim]"
    },
    "info": {
        "analyzing": "[dim]Analyzing {count} tables...[/dim]"
    }
}
