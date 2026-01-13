"""
ISTA MongoDB CLI Tool

Command-line interface for MongoDB test data provisioning, cleanup, and management.
Works with both local MongoDB and MongoDB Atlas.
"""

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import yaml
import json
from datetime import datetime
from pathlib import Path
import os
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

console = Console()

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


class MongoDBClient:
    """Wrapper around MongoDB client for ISTA operations"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.db_name = None
    
    def connect(self, mongodb_uri: str) -> bool:
        """
        Connect to MongoDB
        
        Args:
            mongodb_uri: MongoDB connection string
        
        Returns:
            True if connection successful
        """
        try:
            self.client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000
            )
            
            # Verify connection
            self.client.admin.command('ping')
            
            # Extract database name
            self.db_name = mongodb_uri.split('/')[-1].split('?')[0]
            if not self.db_name:
                self.db_name = "test"
            
            self.db = self.client[self.db_name]
            logger.info(f"Connected to MongoDB: {self.db_name}")
            return True
        
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Connection failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False
    
    def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    def health_check(self) -> bool:
        """Check MongoDB health"""
        try:
            self.db.client.admin.command('ping')
            return True
        except Exception:
            return False


# Global MongoDB client
mongo_client = MongoDBClient()


@click.group()
@click.option('--mongodb-uri', 
              envvar='MONGODB_URI',
              help='MongoDB connection string')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx, mongodb_uri: str, verbose: bool):
    """
    ISTA MongoDB Test Data Automation Tool
    
    Provision, cleanup, and manage test data in MongoDB collections.
    
    Set MONGODB_URI environment variable to avoid passing --mongodb-uri each time:
    
        export MONGODB_URI="mongodb+srv://user:pass@cluster.net/database"
    """
    ctx.ensure_object(dict)
    ctx.obj['mongodb_uri'] = mongodb_uri
    ctx.obj['verbose'] = verbose
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@cli.command()
@click.option('--databases', '-d', multiple=True, required=True,
              help='Collections to provision (can specify multiple: -d users -d movies)')
@click.option('--volumes', '-v', type=str,
              help='Volume per collection as JSON: {"users":50,"movies":100}')
@click.option('--mask/--no-mask', default=True,
              help='Apply PII masking')
@click.option('--clear', is_flag=True,
              help='Clear existing data before provisioning')
@click.pass_context
def provision(ctx, databases: tuple, volumes: Optional[str], mask: bool, clear: bool):
    """
    Provision test data into MongoDB collections
    
    Examples:
    
        # Provision all defined collections
        ista provision -d users -d movies
    
        # Provision with custom volumes
        ista provision -d users -d movies --volumes '{"users":100,"movies":500}'
    
        # Clear and reprovision
        ista provision -d users --clear
    """
    mongodb_uri = ctx.obj['mongodb_uri']
    
    if not mongodb_uri:
        console.print("[red]Error: MONGODB_URI not provided[/red]")
        console.print("Set it via --mongodb-uri or MONGODB_URI environment variable")
        raise click.Abort()
    
    # Connect to MongoDB
    if not mongo_client.connect(mongodb_uri):
        console.print("[red]Failed to connect to MongoDB[/red]", style="bold red")
        raise click.Abort()
    
    try:
        # Parse volumes
        volume_config = {}
        if volumes:
            try:
                volume_config = json.loads(volumes)
            except json.JSONDecodeError:
                console.print("[red]Invalid volumes JSON[/red]")
                raise click.Abort()
        
        # Load data definitions
        def_dir = Path(__file__).parent / "data_definitions" / "mongodb"
        
        if not def_dir.exists():
            console.print(f"[red]Data definitions directory not found: {def_dir}[/red]")
            raise click.Abort()
        
        # Provision each collection
        provisioned_count = 0
        
        for collection_name in databases:
            spec_file = def_dir / f"{collection_name}.yaml"
            
            if not spec_file.exists():
                console.print(f"[yellow]Skipping {collection_name}: definition not found[/yellow]")
                continue
            
            with open(spec_file) as f:
                spec = yaml.safe_load(f)
            
            # Get volume
            volume = volume_config.get(collection_name, 
                                       spec['spec']['volume'].get('count', 100))
            
            # Clear existing data if requested
            if clear:
                mongo_client.db[collection_name].delete_many({})
                console.print(f"[yellow]Cleared {collection_name}[/yellow]")
            
            # Generate and insert documents
            with Progress() as progress:
                task = progress.add_task(
                    f"[cyan]Provisioning {collection_name}...",
                    total=volume
                )
                
                # Import factory based on collection
                from mongo_factories import (
                    MovieFactory, UserFactory, CommentFactory, SessionFactory
                )
                
                factory_map = {
                    'movies': MovieFactory,
                    'users': UserFactory,
                    'comments': CommentFactory,
                    'sessions': SessionFactory
                }
                
                factory = factory_map.get(collection_name)
                if not factory:
                    console.print(f"[red]No factory for {collection_name}[/red]")
                    continue
                
                # Generate documents in batches
                batch_size = 100
                docs_created = 0
                
                for batch_start in range(0, volume, batch_size):
                    batch_end = min(batch_start + batch_size, volume)
                    batch_count = batch_end - batch_start
                    
                    docs = factory.create_batch(batch_count)
                    
                    # Apply masking if requested
                    if mask and collection_name == 'users':
                        for doc in docs:
                            if 'email' in doc:
                                doc['email'] = _mask_email(doc['email'])
                    
                    # Insert batch
                    result = mongo_client.db[collection_name].insert_many(docs)
                    docs_created += len(result.inserted_ids)
                    
                    progress.update(task, advance=batch_count)
            
            # Get collection stats
            stats = mongo_client.db.command('collStats', collection_name)
            size_mb = stats['size'] / (1024 * 1024)
            
            console.print(
                f"[green]✓ {collection_name}:[/green] "
                f"{docs_created} documents ({size_mb:.2f} MB)"
            )
            provisioned_count += docs_created
        
        console.print(f"\n[green bold]Total provisioned: {provisioned_count} documents[/green bold]")
    
    finally:
        mongo_client.disconnect()


@cli.command()
@click.pass_context
def status(ctx):
    """
    Show status of MongoDB provisioning
    
    Displays document counts and sizes for all collections.
    
    Example:
    
        ista status
    """
    mongodb_uri = ctx.obj['mongodb_uri']
    
    if not mongodb_uri:
        console.print("[red]Error: MONGODB_URI not provided[/red]")
        raise click.Abort()
    
    if not mongo_client.connect(mongodb_uri):
        console.print("[red]Failed to connect to MongoDB[/red]")
        raise click.Abort()
    
    try:
        table = Table(title=f"MongoDB Collections: {mongo_client.db_name}")
        table.add_column("Collection", style="cyan", no_wrap=True)
        table.add_column("Documents", style="magenta", justify="right")
        table.add_column("Size (MB)", style="green", justify="right")
        table.add_column("Avg Doc Size (B)", style="yellow", justify="right")
        table.add_column("Indexes", style="blue", justify="right")
        
        total_docs = 0
        total_size = 0
        
        for collection_name in mongo_client.db.list_collection_names():
            stats = mongo_client.db.command('collStats', collection_name)
            
            doc_count = stats.get('count', 0)
            size_bytes = stats.get('size', 0)
            size_mb = size_bytes / (1024 * 1024)
            avg_doc_size = stats.get('avgObjSize', 0)
            index_count = len(stats.get('indexSizes', {}))
            
            table.add_row(
                collection_name,
                str(doc_count),
                f"{size_mb:.2f}",
                str(int(avg_doc_size)),
                str(index_count)
            )
            
            total_docs += doc_count
            total_size += size_mb
        
        console.print(table)
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  Total Documents: {total_docs}")
        console.print(f"  Total Size: {total_size:.2f} MB")
    
    finally:
        mongo_client.disconnect()


@cli.command()
@click.option('--collections', '-c', multiple=True,
              help='Collections to cleanup (all if not specified)')
@click.option('--force', is_flag=True,
              help='Skip confirmation prompt')
@click.pass_context
def cleanup(ctx, collections: tuple, force: bool):
    """
    Clean up test data from MongoDB
    
    Deletes all documents from specified collections.
    
    Examples:
    
        # Delete from specific collections
        ista cleanup -c users -c movies
    
        # Delete from all collections (with confirmation)
        ista cleanup
    
        # Skip confirmation
        ista cleanup --force
    """
    mongodb_uri = ctx.obj['mongodb_uri']
    
    if not mongodb_uri:
        console.print("[red]Error: MONGODB_URI not provided[/red]")
        raise click.Abort()
    
    if not mongo_client.connect(mongodb_uri):
        console.print("[red]Failed to connect to MongoDB[/red]")
        raise click.Abort()
    
    try:
        target_collections = list(collections) if collections else mongo_client.db.list_collection_names()
        
        if not force:
            console.print(f"[yellow]Will delete data from:[/yellow]")
            for c in target_collections:
                console.print(f"  - {c}")
            
            if not click.confirm("Continue?"):
                console.print("[yellow]Cleanup cancelled[/yellow]")
                return
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Cleaning up...", total=len(target_collections))
            
            for collection_name in target_collections:
                result = mongo_client.db[collection_name].delete_many({})
                console.print(f"[green]✓ {collection_name}:[/green] Deleted {result.deleted_count} documents")
                progress.update(task, advance=1)
        
        console.print("[green bold]Cleanup complete[/green bold]")
    
    finally:
        mongo_client.disconnect()


@cli.command()
@click.option('--collection', '-c', required=True,
              help='Collection to query')
@click.option('--limit', '-l', default=5,
              help='Number of documents to show')
@click.pass_context
def show(ctx, collection: str, limit: int):
    """
    Display sample documents from a collection
    
    Shows first N documents as JSON.
    
    Example:
    
        ista show -c movies --limit 3
    """
    mongodb_uri = ctx.obj['mongodb_uri']
    
    if not mongodb_uri:
        console.print("[red]Error: MONGODB_URI not provided[/red]")
        raise click.Abort()
    
    if not mongo_client.connect(mongodb_uri):
        console.print("[red]Failed to connect to MongoDB[/red]")
        raise click.Abort()
    
    try:
        docs = list(mongo_client.db[collection].find().limit(limit))
        
        if not docs:
            console.print(f"[yellow]No documents found in {collection}[/yellow]")
            return
        
        console.print(f"[cyan]Sample documents from {collection}:[/cyan]\n")
        
        for i, doc in enumerate(docs, 1):
            # Convert ObjectId to string for JSON serialization
            json_str = json.dumps(doc, indent=2, default=str)
            console.print(f"[bold cyan]Document {i}:[/bold cyan]")
            console.print(json_str)
            console.print()
    
    finally:
        mongo_client.disconnect()


@cli.command()
@click.pass_context
def health(ctx):
    """
    Check MongoDB connection health
    
    Verifies connection and displays server info.
    
    Example:
    
        ista health
    """
    mongodb_uri = ctx.obj['mongodb_uri']
    
    if not mongodb_uri:
        console.print("[red]Error: MONGODB_URI not provided[/red]")
        raise click.Abort()
    
    if mongo_client.connect(mongodb_uri):
        try:
            # Get server info
            server_info = mongo_client.db.client.server_info()
            
            console.print("[green]✓ MongoDB connection healthy[/green]")
            console.print(f"  Database: {mongo_client.db_name}")
            console.print(f"  Version: {server_info.get('version', 'unknown')}")
            console.print(f"  Collections: {len(mongo_client.db.list_collection_names())}")
            
            # Check Atlas if applicable
            if 'mongodb+srv://' in mongodb_uri:
                console.print("  Cluster: MongoDB Atlas")
        
        finally:
            mongo_client.disconnect()
    else:
        console.print("[red]✗ MongoDB connection failed[/red]")
        raise click.Abort()


def _mask_email(email: str) -> str:
    """Mask email address"""
    import re
    match = re.match(r'(\w)(\w*)@(.+)', email)
    if match:
        return f"{match.group(1)}***@{match.group(3)}"
    return "masked@example.com"


if __name__ == '__main__':
    cli(obj={})
