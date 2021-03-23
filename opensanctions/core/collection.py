from opensanctions.core.dataset import Dataset
from opensanctions.core.source import Source


class Collection(Dataset):
    """A grouping of individual data sources. Data sources are bundled in order
    to be more useful for list use."""

    TYPE = "collection"

    def __init__(self, file_path, config):
        super().__init__(self.TYPE, file_path, config)

    @property
    def sources(self):
        datasets = set()
        for dataset in Dataset.all():
            if self.name in dataset.collections:
                datasets.update(dataset.sources)
        return set([t for t in datasets if t.TYPE == Source.TYPE])
