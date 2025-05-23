"""
Configuration and database synchronization module, responsible for syncing 
information from configuration files to the database, with config as the source of truth.
"""
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from forager.storage.sqlite import SQLiteStorage
from forager.config.manager import ConfigManager, FeedConfig

class ConfigSynchronizer:
    """Class responsible for synchronization between YAML configuration and database"""
    
    def __init__(self, config_path: Path, storage: SQLiteStorage, debug: bool = False):
        """
        Initialize the configuration synchronizer
        
        Args:
            config_path (Path): Path to configuration file
            storage (SQLiteStorage): Database storage object
            debug (bool): Whether to enable debug mode
        """
        self.config_path = config_path
        self.storage = storage
        self.debug = debug
        self.config_manager = ConfigManager(config_path)
        # Load configuration
        self.config_manager.load()
    
    def sync_categories(self) -> Dict[str, int]:
        """
        Synchronize all categories, ensuring categories in config exist in the database
        
        Returns:
            Dict[str, int]: Mapping of category names to category IDs
        """
        feeds = self.config_manager.get_enabled_feeds()
        feed_dicts = [feed.__dict__ if hasattr(feed, '__dict__') else feed for feed in feeds]
        
        # Extract all categories from config
        category_names = set(
            getattr(feed, 'category', None) or (feed.get('category') if isinstance(feed, dict) else None) or 'Default'
            for feed in feed_dicts
        )
        category_names = set(name.strip() for name in category_names)
        
        # Query existing categories in database
        db_categories = self.storage.get_categories()
        db_category_map = {c['name']: c['id'] for c in db_categories}
        
        # Insert missing categories
        for name in category_names:
            if name not in db_category_map:
                new_id = self.storage.create_category(name)
                db_category_map[name] = new_id
                if self.debug:
                    print(f"[DEBUG] Created new category: {name} (ID: {new_id})")
        
        print(f"[INFO] Synchronized categories from config: {category_names}")
        return db_category_map
    
    def sync_feeds(self, print_summary: bool = True) -> Dict[str, Any]:
        """
        Synchronize all feed information, with config as the source of truth
        
        Args:
            print_summary (bool): Whether to print summary information at the end
            
        Returns:
            Dict[str, Any]: Synchronization result statistics
        """
        # First sync categories to get mapping
        category_map = self.sync_categories()
        
        # Get ALL feeds from config (both enabled and disabled)
        self.config_manager.load()
        self.config_manager.validate()
        all_config_feeds = self.config_manager._feeds  # Get all feeds, not just enabled ones
        
        # Get existing feeds from database
        db_feeds = self.storage.get_feeds()
        db_feeds_by_url = {feed['url']: feed for feed in db_feeds}
        
        # Get all tags from database
        db_tags = self.storage.get_tags()
        db_tags_by_name = {tag['name'].lower(): tag['id'] for tag in db_tags}
        
        results = {
            'created': 0,
            'updated': 0,
            'deleted': 0,
            'unchanged': 0,
            'errors': []
        }
        
        # Process feeds from config
        config_feed_urls = set()
        for feed in all_config_feeds:
            try:
                config_feed_urls.add(feed.url)
                category_name = getattr(feed, 'category', None) or 'Default'
                category_id = category_map.get(category_name.strip(), category_map.get('Default'))
                
                # Determine status based on enabled flag
                desired_status = "active" if feed.enabled else "disabled"
                
                if self.debug:
                    print(f"[DEBUG] Processing feed: {feed.name} ({feed.url}), category: {category_name}, enabled: {feed.enabled}")
                
                # Process tags (only for enabled feeds)
                feed_tags = getattr(feed, 'tags', []) or [] if feed.enabled else []
                tag_ids = []
                
                # Ensure all tags exist in database (only for enabled feeds)
                if feed.enabled:
                    for tag_name in feed_tags:
                        if not tag_name:
                            continue
                            
                        tag_name_lower = tag_name.lower().strip()
                        if tag_name_lower in db_tags_by_name:
                            tag_ids.append(db_tags_by_name[tag_name_lower])
                            if self.debug:
                                print(f"[DEBUG] Using existing tag: {tag_name} (ID: {db_tags_by_name[tag_name_lower]})")
                        else:
                            # Create new tag
                            new_tag_id = self.storage.create_tag(tag_name)
                            db_tags_by_name[tag_name_lower] = new_tag_id
                            tag_ids.append(new_tag_id)
                            if self.debug:
                                print(f"[DEBUG] Created new tag: {tag_name} (ID: {new_tag_id})")
                
                if feed.url in db_feeds_by_url:
                    # Update existing feed
                    db_feed = db_feeds_by_url[feed.url]
                    updates = {}
                    
                    if feed.name != db_feed['name']:
                        updates['name'] = feed.name
                        if self.debug:
                            print(f"[DEBUG] Updating feed name: {db_feed['name']} -> {feed.name}")
                    
                    if feed.interval != db_feed['poll_interval']:
                        updates['poll_interval'] = feed.interval
                        if self.debug:
                            print(f"[DEBUG] Updating feed poll interval: {db_feed['poll_interval']} -> {feed.interval}")
                    
                    if category_id != db_feed['category_id']:
                        updates['category_id'] = category_id
                        if self.debug:
                            print(f"[DEBUG] Updating feed category ID: {db_feed['category_id']} -> {category_id}")
                            
                    # Update string_id with the feed's id from config
                    if hasattr(feed, 'id') and feed.id:
                        if self.debug:
                            print(f"[DEBUG] Checking string_id update: current={db_feed.get('string_id')}, config={feed.id}")
                        
                        if db_feed.get('string_id') != feed.id:
                            updates['string_id'] = feed.id
                            if self.debug:
                                print(f"[DEBUG] Updating feed string_id: {db_feed.get('string_id')} -> {feed.id}")
                                print(f"[DEBUG] Feed ID in database: {db_feed['id']}")
                    
                    # Update status based on enabled flag
                    if desired_status != db_feed['status']:
                        updates['status'] = desired_status
                        if self.debug:
                            print(f"[DEBUG] Updating feed status: {db_feed['status']} -> {desired_status}")
                    
                    if updates:
                        if self.debug:
                            print(f"[DEBUG] Update details: {updates}")
                            
                        success = self.storage.update_feed(db_feed['id'], updates)
                        if self.debug:
                            print(f"[DEBUG] Update operation success: {success}")
                            
                        results['updated'] += 1
                        if self.debug:
                            print(f"[DEBUG] Updated feed: {feed.url}")
                            # After update, fetch the feed again to verify changes
                            updated_feed = self.storage.get_feed(db_feed['id'])
                            if updated_feed:
                                print(f"[DEBUG] Feed after update: string_id={updated_feed.get('string_id')}, status={updated_feed.get('status')}")
                            else:
                                print(f"[DEBUG] Could not retrieve updated feed")
                    else:
                        results['unchanged'] += 1
                        if self.debug:
                            print(f"[DEBUG] Feed properties unchanged: {feed.url}")
                            
                    # Sync tags (only for enabled feeds)
                    if feed.enabled:
                        feed_id = db_feed['id']
                        
                        # Add tags to the feed
                        if tag_ids:
                            try:
                                # Use SQLiteStorage methods to get feed tags
                                # For each tag ID, check if it's already associated with the feed
                                for tag_id in tag_ids:
                                    # Check if tag exists in the feed_tags table for this feed
                                    # If not, add it
                                    self.storage.add_tag_to_feed(feed_id, tag_id)
                                    
                                if self.debug:
                                    print(f"[DEBUG] Added tags to feed {feed_id}: {tag_ids}")
                            except Exception as e:
                                if self.debug:
                                    print(f"[DEBUG] Error syncing tags for feed {feed_id}: {str(e)}")
                else:
                    # Create new feed
                    feed_id = self.storage.create_feed(
                        category_id=category_id,
                        name=feed.name,
                        url=feed.url,
                        poll_interval=feed.interval,
                        status=desired_status
                    )
                    
                    # Set string_id using the feed's id from config
                    if hasattr(feed, 'id') and feed.id:
                        self.storage.update_feed(feed_id, {'string_id': feed.id})
                        if self.debug:
                            print(f"[DEBUG] Set string_id for new feed: {feed.id}")
                    
                    results['created'] += 1
                    if self.debug:
                        print(f"[DEBUG] Created new feed (ID: {feed_id}): {feed.name} ({feed.url}) with status: {desired_status}")
                        
                    # Add tags to the new feed (only for enabled feeds)
                    if feed.enabled and tag_ids:
                        for tag_id in tag_ids:
                            self.storage.add_tag_to_feed(feed_id, tag_id)
                        if self.debug:
                            print(f"[DEBUG] Added tags to new feed {feed_id}: {tag_ids}")
            except Exception as e:
                error_msg = f"Error processing feed {feed.url}: {str(e)}"
                results['errors'].append(error_msg)
                print(f"[ERROR] {error_msg}")
                if self.debug:
                    import traceback
                    print(f"[DEBUG] Error details:\n{traceback.format_exc()}")
        
        # Handle feeds that should be deleted (in database but not in config)
        # Get delete_missing option from config
        enable_delete = False
        try:
            # Try to get sync options from config
            sync_config = self.config_manager._config.get('sync', {}) if self.config_manager._config else {}
            if isinstance(sync_config, dict):
                enable_delete = sync_config.get('delete_missing', False)
                if self.debug:
                    print(f"[DEBUG] Config delete_missing option: {enable_delete}")
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Error getting delete_missing config option: {str(e)}")
            pass  # Default to not deleting if unable to get config options
            
        if enable_delete:
            for db_feed in db_feeds:
                if db_feed['url'] not in config_feed_urls:
                    # Mark as deleted
                    self.storage.update_feed(db_feed['id'], {'status': 'deleted'})
                    results['deleted'] += 1
                    if self.debug:
                        print(f"[DEBUG] Marked feed as deleted: {db_feed['url']}")
        
        # Print summary if requested
        if print_summary:
            print(f"[INFO] Synchronization completed:")
            print(f"  - Created: {results['created']}")
            print(f"  - Updated: {results['updated']}")
            print(f"  - Deleted: {results['deleted']}")
            print(f"  - Unchanged: {results['unchanged']}")
            
            if results['errors']:
                print(f"[WARNING] Encountered {len(results['errors'])} errors during synchronization")
            
        return results
    
    @classmethod
    def sync_categories_from_config(cls, config_feeds, storage) -> dict:
        """
        Legacy API compatible category synchronization method
        
        Args:
            config_feeds: Feed list from config
            storage: Database storage object
            
        Returns:
            dict: Mapping of category names to category IDs
        """
        # Extract all categories from config
        category_names = set(
            getattr(feed, 'category', None) or (feed.get('category') if isinstance(feed, dict) else None) or 'Default'
            for feed in config_feeds
        )
        category_names = set(name.strip() for name in category_names)
        
        # Query existing categories in database
        db_categories = storage.get_categories()
        db_category_map = {c['name']: c['id'] for c in db_categories}
        
        # Insert missing categories
        for name in category_names:
            if name not in db_category_map:
                new_id = storage.create_category(name)
                db_category_map[name] = new_id
                
        print(f"[INFO] Synchronized categories: {category_names}")
        return db_category_map 