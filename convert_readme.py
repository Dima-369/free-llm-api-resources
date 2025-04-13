#!/usr/bin/env python3

import re
import sys
from bs4 import BeautifulSoup

def convert_table_to_markdown(html_table):
    """Convert an HTML table to Markdown with nested headings and bullet points."""
    soup = BeautifulSoup(html_table, 'html.parser')

    # Extract table headers
    headers = []
    for th in soup.find_all('th'):
        headers.append(th.get_text().strip())

    # Process table rows
    result = ""
    current_provider = None
    current_provider_limits = None

    for tr in soup.find_all('tr'):
        tds = tr.find_all('td')
        if not tds:
            continue

        # Check if this row has a provider (first column)
        provider_cell = None
        if 'rowspan' in tr.find_all('td')[0].attrs:
            provider_cell = tr.find_all('td')[0]
            provider_name = provider_cell.find('a').get_text().strip() if provider_cell.find('a') else provider_cell.get_text().strip()
            provider_url = provider_cell.find('a')['href'] if provider_cell.find('a') else None

            # Get provider limits (second column)
            provider_limits_cell = tr.find_all('td')[1]
            provider_limits = provider_limits_cell.get_text().strip().replace('<br>', ', ').replace('minute', 'minute, ').replace('hour', 'hour, ').replace('day', 'day, ')
            # Clean up any double commas or trailing commas
            provider_limits = re.sub(r', ,', ',', provider_limits)
            provider_limits = re.sub(r', $', '', provider_limits)

            # Add provider as a second-level heading
            result += f"\n## [{provider_name}]({provider_url})\n\n"
            result += f"**Provider Limits/Notes**: {provider_limits}\n\n"
            result += "### Models\n\n"

            # Update current provider
            current_provider = provider_name
            current_provider_limits = provider_limits

            # Get model info from the remaining columns
            model_cell_index = 2
        else:
            # This row continues with the current provider
            model_cell_index = 0

        # Extract model information
        if len(tds) > model_cell_index:
            model_cell = tds[model_cell_index]
            model_name = model_cell.find('a').get_text().strip() if model_cell.find('a') else model_cell.get_text().strip()
            model_url = model_cell.find('a')['href'] if model_cell.find('a') else None

            # Extract model limits if available
            model_limits = ""
            if len(tds) > model_cell_index + 1:
                limits_cell = tds[model_cell_index + 1]
                model_limits = limits_cell.get_text().strip().replace('<br>', ', ').replace('minute', 'minute, ').replace('hour', 'hour, ').replace('day', 'day, ')
                # Clean up any double commas or trailing commas
                model_limits = re.sub(r', ,', ',', model_limits)
                model_limits = re.sub(r', $', '', model_limits)

            # Add model as a bullet point
            if model_url:
                result += f"- [{model_name}]({model_url})"
            else:
                result += f"- **{model_name}**"

            if model_limits:
                result += f" - {model_limits}"

            result += "\n"

    return result

def process_trial_providers(content):
    """Special handling for the trial providers section."""
    trial_section_pattern = re.compile(r'## Providers with trial credits\s*\n(.*?)\n\n', re.DOTALL)
    trial_section_match = trial_section_pattern.search(content)

    if trial_section_match:
        trial_section = trial_section_match.group(1)
        # Format the trial providers section better
        formatted_section = "\n## Providers with Trial Credits\n\n"

        # Extract each provider line
        provider_pattern = re.compile(r'- \[(.*?)\]\((.*?)\) - (.*?)(?:\n|$)')
        providers = provider_pattern.findall(trial_section)

        for provider_name, provider_url, provider_details in providers:
            formatted_section += f"### [{provider_name}]({provider_url})\n\n"
            formatted_section += f"**Credits**: {provider_details}\n\n"

        # Replace the original section with the formatted one
        content = trial_section_pattern.sub(formatted_section, content)

    return content

def process_readme(input_file, output_file):
    with open(input_file, 'r') as f:
        content = f.read()

    # Find all tables in the content
    table_pattern = re.compile(r'<table>.*?</table>', re.DOTALL)
    tables = table_pattern.findall(content)

    # Process each table
    for table in tables:
        markdown = convert_table_to_markdown(table)
        content = content.replace(table, markdown)

    # Special handling for trial providers section
    content = process_trial_providers(content)

    # Remove any empty tbody or thead tags that might be left
    content = re.sub(r'<tbody>|</tbody>|<thead>|</thead>', '', content)

    # Write the result to the output file
    with open(output_file, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    input_file = "README.md"
    output_file = "README_new.md"

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    process_readme(input_file, output_file)
    print(f"Converted {input_file} to {output_file}")
