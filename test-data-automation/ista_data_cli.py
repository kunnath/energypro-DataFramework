#!/usr/bin/env python3
"""
ISTA (Infrastructure for Seamless Test Automation)
Test Data Provisioning CLI Tool

Usage:
  ista-data provision --datasets users,orders --volumes '{"users":100,"orders":500}'
  ista-data status abc-123-def
  ista-data cleanup abc-123-def
"""

import click
import json
import requests
import yaml
from typing import Dict, List
from datetime import datetime

# Configuration
API_ENDPOINT = "http://localhost:8000"
LOG_LEVEL = "INFO"

@click.group()
@click.version_option("1.0.0")
def cli():
    """ISTA Data Provisioning CLI Tool"""
    pass

@cli.command()
@click.option('--datasets', type=str, required=True, help='Comma-separated dataset names')
@click.option('--volumes', type=str, help='JSON volumes per dataset')
@click.option('--mask/--no-mask', default=True, help='Apply PII masking')
@click.option('--version', type=str, default='latest', help='Data spec version')
@click.option('--ttl', type=int, default=120, help='Time to live (minutes)')
def provision(datasets: str, volumes: str, mask: bool, version: str, ttl: int):
    """
    Provision test data.
    
    Examples:
    \b
    # Basic provisioning
    $ ista-data provision --datasets users,orders
    
    # With custom volumes
    $ ista-data provision --datasets users,orders \\
      --volumes '{"users":100,"orders":500}' --version v1.0.0
    
    # Without masking (for non-sensitive testing)
    $ ista-data provision --datasets products --no-mask
    """
    dataset_list = [d.strip() for d in datasets.split(',')]
    
    # Parse volumes
    volumes_dict = {}
    if volumes:
        try:
            volumes_dict = json.loads(volumes)
        except json.JSONDecodeError:
            click.echo(click.style("✗ Invalid JSON for volumes", fg='red'), err=True)
            return
    else:
        volumes_dict = {d: 100 for d in dataset_list}
    
    # Build request
    request_payload = {
        "datasets": dataset_list,
        "volumes": volumes_dict,
        "apply_masking": mask,
        "version": version,
        "ttl_minutes": ttl
    }
    
    click.echo(click.style("📊 Provisioning test data...", fg='cyan'))
    click.echo(f"  Datasets: {', '.join(dataset_list)}")
    click.echo(f"  Volumes: {json.dumps(volumes_dict)}")
    click.echo(f"  Masking: {'Enabled' if mask else 'Disabled'}")
    click.echo(f"  TTL: {ttl} minutes")
    click.echo()
    
    try:
        response = requests.post(
            f"{API_ENDPOINT}/provision",
            json=request_payload,
            timeout=300
        )
        
        if response.status_code == 200:
            result = response.json()
            
            click.echo(click.style("✓ Provisioning successful!", fg='green'))
            click.echo(f"  Request ID: {click.style(result['request_id'], fg='bright_cyan')}")
            click.echo(f"  Status: {result['status']}")
            click.echo()
            click.echo(click.style("  Records Provisioned:", fg='blue', bold=True))
            for dataset, count in result['record_counts'].items():
                click.echo(f"    • {dataset}: {click.style(str(count), fg='green')} rows")
            
            click.echo()
            click.echo(f"  Expires at: {result['expires_at']}")
            click.echo()
            click.echo(click.style(f"  💾 Save request ID: {result['request_id']}", fg='yellow'))
        else:
            click.echo(click.style(f"✗ Provisioning failed: {response.text}", fg='red'), err=True)
            exit(1)
    
    except requests.exceptions.Timeout:
        click.echo(click.style("✗ Request timed out. Data may still be provisioning.", fg='yellow'), err=True)
    except requests.exceptions.RequestException as e:
        click.echo(click.style(f"✗ Error: {str(e)}", fg='red'), err=True)
        exit(1)

@cli.command()
@click.argument('request_id')
def status(request_id: str):
    """Check provisioning status"""
    try:
        response = requests.get(f"{API_ENDPOINT}/provision/{request_id}")
        
        if response.status_code == 200:
            result = response.json()
            
            status_color = 'green' if result['status'] == 'success' else 'yellow'
            click.echo(f"Status: {click.style(result['status'], fg=status_color)}")
            click.echo(f"Datasets: {', '.join(result['datasets_provisioned'])}")
            click.echo()
            click.echo(click.style("Records:", fg='blue', bold=True))
            for dataset, count in result['record_counts'].items():
                click.echo(f"  • {dataset}: {count}")
            
            click.echo()
            click.echo(f"Provisioned at: {result['provisioned_at']}")
            click.echo(f"Expires at: {result['expires_at']}")
        else:
            click.echo(click.style(f"✗ Request not found: {request_id}", fg='red'), err=True)
            exit(1)
    
    except requests.exceptions.RequestException as e:
        click.echo(click.style(f"✗ Error: {str(e)}", fg='red'), err=True)
        exit(1)

@cli.command()
@click.argument('request_id')
@click.option('--force', is_flag=True, help='Force cleanup without confirmation')
def cleanup(request_id: str, force: bool):
    """Cleanup provisioned data"""
    
    if not force:
        if not click.confirm(f"Delete data provisioned under request {request_id}?"):
            click.echo("Cleanup cancelled.")
            return
    
    try:
        response = requests.delete(f"{API_ENDPOINT}/provision/{request_id}")
        
        if response.status_code == 200:
            click.echo(click.style(f"✓ Cleaned up {request_id}", fg='green'))
        else:
            click.echo(click.style(f"✗ Cleanup failed: {response.text}", fg='red'), err=True)
            exit(1)
    
    except requests.exceptions.RequestException as e:
        click.echo(click.style(f"✗ Error: {str(e)}", fg='red'), err=True)
        exit(1)

@cli.command()
@click.option('--dataset', type=str, required=True, help='Dataset name')
def show_spec(dataset: str):
    """Show data specification for dataset"""
    try:
        with open(f"test-data-automation/data_definitions/{dataset}.yaml") as f:
            spec = yaml.safe_load(f)
        
        click.echo(click.style(f"Data Specification: {dataset}", fg='cyan', bold=True))
        click.echo("=" * 60)
        click.echo(yaml.dump(spec, default_flow_style=False, sort_keys=False))
    
    except FileNotFoundError:
        click.echo(click.style(f"✗ Spec not found for dataset: {dataset}", fg='red'), err=True)
        exit(1)

@cli.command()
def list_datasets():
    """List available datasets"""
    import os
    from pathlib import Path
    
    spec_dir = Path("test-data-automation/data_definitions")
    
    if not spec_dir.exists():
        click.echo(click.style("✗ Data definitions directory not found", fg='red'), err=True)
        return
    
    datasets = [f.stem for f in spec_dir.glob("*.yaml")]
    
    click.echo(click.style("Available Datasets:", fg='cyan', bold=True))
    for dataset in sorted(datasets):
        try:
            with open(spec_dir / f"{dataset}.yaml") as f:
                spec = yaml.safe_load(f)
                description = spec.get('metadata', {}).get('description', 'No description')
                volume = spec.get('spec', {}).get('volume', {}).get('count', 'Unknown')
                click.echo(f"  • {click.style(dataset, fg='green')}")
                click.echo(f"    └─ {description} ({volume} rows)")
        except Exception:
            click.echo(f"  • {dataset}")

@cli.command()
def health():
    """Check API health"""
    try:
        response = requests.get(f"{API_ENDPOINT}/health", timeout=5)
        
        if response.status_code == 200:
            click.echo(click.style("✓ API is healthy", fg='green'))
        else:
            click.echo(click.style("✗ API returned error", fg='red'), err=True)
            exit(1)
    
    except requests.exceptions.RequestException:
        click.echo(click.style(f"✗ Cannot reach API at {API_ENDPOINT}", fg='red'), err=True)
        exit(1)

if __name__ == '__main__':
    cli()
