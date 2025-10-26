"""
Ollama Library Scraper Service

Scrapes and caches model information from ollama.com/library
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class OllamaLibraryScraper:
    """Scrapes and caches model information from Ollama library"""

    LIBRARY_URL = "https://ollama.com/library"
    CACHE_TTL_HOURS = 24

    def __init__(self):
        self._cache: Optional[List[Dict]] = None
        self._cache_time: Optional[datetime] = None

    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid"""
        if self._cache is None or self._cache_time is None:
            return False

        age = datetime.now() - self._cache_time
        return age < timedelta(hours=self.CACHE_TTL_HOURS)

    def _parse_model_tags(self, tags_text: str) -> Dict[str, List[str]]:
        """Parse tags and sizes from tag text"""
        tags = []
        sizes = []

        parts = tags_text.strip().split()
        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Check if it's a size (ends with 'b' or 'B' and starts with digit)
            if part.lower().endswith('b') and part[:-1].replace('.', '').isdigit():
                sizes.append(part)
            else:
                tags.append(part)

        return {'tags': tags, 'sizes': sizes}

    def _estimate_model_size(self, param_size: str) -> str:
        """Estimate model download size based on parameter count"""
        try:
            # Remove 'b' and convert to float
            params = float(param_size.lower().rstrip('b'))

            # Rough estimation:
            # - Small models (< 3B): ~1-2 GB per billion parameters
            # - Medium models (3-13B): ~0.6-0.8 GB per billion parameters
            # - Large models (> 13B): ~0.5-0.6 GB per billion parameters
            # This accounts for quantization (typically 4-bit or 8-bit)

            if params < 1:
                size_gb = params * 0.5  # Sub-billion models
            elif params < 3:
                size_gb = params * 1.5
            elif params < 13:
                size_gb = params * 0.7
            else:
                size_gb = params * 0.55

            # Format the size nicely
            if size_gb < 1:
                return f"~{int(size_gb * 1024)}MB"
            else:
                return f"~{size_gb:.1f}GB"
        except (ValueError, AttributeError):
            return "Size unknown"

    def _categorize_model(self, tags: List[str], name: str, description: str) -> str:
        """Categorize model based on tags, name, and description"""
        tags_lower = [t.lower() for t in tags]
        name_lower = name.lower()
        desc_lower = description.lower()

        # Check for embedding models
        if 'embedding' in tags_lower or 'embed' in name_lower:
            return 'embedding'

        # Check for vision models
        if 'vision' in tags_lower or 'multimodal' in tags_lower:
            return 'vision'

        # Check for code models
        if 'code' in tags_lower or 'coding' in desc_lower:
            return 'code'

        # Check for reasoning models
        if 'reasoning' in tags_lower or 'thinking' in tags_lower or 'reason' in desc_lower:
            return 'reasoning'

        # Check for tools/function calling
        if 'tools' in tags_lower or 'function' in desc_lower:
            return 'tools'

        # Default to generation
        return 'generation'

    def _scrape_library(self) -> List[Dict]:
        """Scrape model information from Ollama library"""
        try:
            logger.info(f"Scraping Ollama library: {self.LIBRARY_URL}")
            response = requests.get(self.LIBRARY_URL, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            models = []

            # Find all model list items
            model_items = soup.find_all('li')

            for item in model_items:
                try:
                    # Find the link and model name
                    link = item.find('a')
                    if not link or not link.get('href', '').startswith('/library/'):
                        continue

                    # Extract model name from href
                    href = link.get('href', '')
                    model_name = href.replace('/library/', '')

                    # Extract h2 (model display name)
                    h2 = link.find('h2')
                    if not h2:
                        continue
                    # Get the span inside h2 that contains the actual name
                    name_span = h2.find('span', class_='group-hover:underline')
                    display_name = name_span.get_text(strip=True) if name_span else model_name

                    # Extract description - first p tag with text
                    description_p = link.find('p', class_='max-w-lg')
                    description = description_p.get_text(strip=True) if description_p else ''

                    # Extract tags and sizes from span elements
                    tags = []
                    sizes = []

                    # Find all capability and size spans
                    capability_spans = link.find_all('span', attrs={'x-test-capability': ''})
                    for span in capability_spans:
                        tags.append(span.get_text(strip=True))

                    size_spans = link.find_all('span', attrs={'x-test-size': ''})
                    size_info = []
                    for span in size_spans:
                        param_size = span.get_text(strip=True)
                        sizes.append(param_size)
                        # Create size info with estimated download size
                        estimated_size = self._estimate_model_size(param_size)
                        size_info.append({
                            'param_size': param_size,
                            'download_size': estimated_size
                        })

                    parsed_tags = {'tags': tags, 'sizes': sizes}

                    # Extract stats (pulls, tags, updated)
                    stats_div = link.find('div', class_='stats')
                    stats_text = stats_div.get_text(strip=True) if stats_div else ''

                    # Categorize the model
                    category = self._categorize_model(
                        parsed_tags['tags'],
                        model_name,
                        description
                    )

                    model_info = {
                        'name': model_name,
                        'display_name': display_name,
                        'description': description,
                        'tags': parsed_tags['tags'],
                        'sizes': parsed_tags['sizes'],
                        'size_info': size_info,  # Detailed size information
                        'category': category,
                        'stats': stats_text
                    }

                    models.append(model_info)

                except Exception as e:
                    logger.warning(f"Error parsing model item: {e}")
                    continue

            logger.info(f"Successfully scraped {len(models)} models from Ollama library")
            return models

        except Exception as e:
            logger.error(f"Error scraping Ollama library: {e}")
            return []

    def get_models(self, force_refresh: bool = False) -> List[Dict]:
        """Get all models from library (cached or fresh)"""
        if force_refresh or not self._is_cache_valid():
            self._cache = self._scrape_library()
            self._cache_time = datetime.now()

        return self._cache or []

    def search_models(self, query: str, category: Optional[str] = None) -> List[Dict]:
        """Search models by query and optionally filter by category"""
        models = self.get_models()

        if not query and not category:
            return models

        results = []
        query_lower = query.lower() if query else ''

        for model in models:
            # Filter by category if specified
            if category and model['category'] != category:
                continue

            # Search in name, display_name, description, and tags
            if query_lower:
                searchable_text = (
                    model['name'].lower() + ' ' +
                    model['display_name'].lower() + ' ' +
                    model['description'].lower() + ' ' +
                    ' '.join(model['tags']).lower()
                )

                if query_lower not in searchable_text:
                    continue

            results.append(model)

        return results

    def get_categories(self) -> List[str]:
        """Get list of all categories"""
        return ['generation', 'embedding', 'vision', 'code', 'reasoning', 'tools']


# Global instance
_scraper = OllamaLibraryScraper()


def get_scraper() -> OllamaLibraryScraper:
    """Get the global scraper instance"""
    return _scraper
