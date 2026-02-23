import typing as tp
from enum import Enum
from pathlib import Path
from copy import deepcopy

class LevelType(Enum):
    MODEL = 1
    FOLDER = 2
    PICK_ONE = 3

class Level:
    def __init__(self, name:str, level_type:LevelType, force_folder:str="") -> None:
        """
            :param self: Abstraction for certain depth in a directory tree

            :type name: str
            :type level_type: LevelType

            :param force_folder: Force only using this folder when exploring the level. e.g., there are the inference and checkpoint folders, but you only want to explore the inference folder 
            :type force_folder: str
        """

        self.name = name
        self.type = level_type
        self.force_folder = force_folder

    @property
    def is_force_folder(self):
        return len(self.force_folder) > 0

class ModelData:
    def __init__(
            self, 
            name:str, 
            path:Path, 
            ends_with:str, 
            levels:tp.List[Level]
        ):
        self.name = name
        self.path = path
        self.ends_with = ends_with
        self.levels = levels

        self.contents:tp.List[Path] = []

class LikertQuestion:
    def __init__(self, header:str, options:tp.List[str]) -> None:
        self.header = header
        self.options = options

        assert len(options) == 5, "len options in LikertQuestion should be == 5"

class StudyTemplate:
    def __init__(
            self, 
            name:str,
            n_experiments:int,
            n_models:int,
            levels:tp.List[Level], 
            questions:tp.List[LikertQuestion],
            gt_questions:tp.List[LikertQuestion],
            gt="Ground_Truth",
            gt_ends_with=".mp4",
            gen_ends_with="_gen.mp4", 
        ) -> None:

        self.name = name

        self.src_dir = Path(__file__).resolve().parent
        self.experiments_dir = self.src_dir.joinpath('./static/experiments')
        self.n_experiments = n_experiments
        self.n_models = n_models
        self.questions = questions
        self.gt_questions = gt_questions
        self.gt = gt
        self.gt_ends_with = gt_ends_with
        self.gen_ends_with = gen_ends_with

        self.models:tp.List[ModelData] = []
        self.first_non_gt:ModelData = None # type: ignore

        self._pick_one_dict:tp.Dict[str, tp.List[Path]] = {}
        self._explore_model_level(gt, gt_ends_with, gen_ends_with, levels)
        self._discover_pick_one_dict_keys()
        self._get_pick_one_values()
        self._set_models_paths()

    def _explore_model_level(self, gt:str, gt_ends_with:str, gen_ends_with:str, levels):
        """
            Get models names and paths, appending them to the Template models list
        """
        for dir in sorted(self.experiments_dir.iterdir()):
            full_path = self.experiments_dir.joinpath(dir)

            if dir.name == gt:
                new_model = ModelData(dir.name, full_path, gt_ends_with, deepcopy(levels[1:]))
            else:
                new_model = ModelData(dir.name, full_path, gen_ends_with, deepcopy(levels[1:]))

                if self.first_non_gt == None:
                    self.first_non_gt = new_model

            self.models.append(new_model)

    def _discover_pick_one_dict_keys(self):
        """
            Set _pick_one_dict keys defining the path to be traveled up until the PICK_ONE level
            This path should be equal for every model
        """
        # Only need to explore the levels of one random model
        current_dir = self.first_non_gt.path
        relative_dir = ""

        for level in self.first_non_gt.levels:
            if level.type == LevelType.FOLDER:
                assert level.is_force_folder, "All levels before PICK_ONE must have force_folder set"

                current_dir = current_dir.joinpath(level.force_folder)
                if len(relative_dir) == 0:
                    relative_dir = level.force_folder
                else:
                    relative_dir += f"{level.force_folder}"

            if level.type == LevelType.PICK_ONE:
                for folder in current_dir.iterdir():
                    key = relative_dir + f"/{folder.name}"
                    self._pick_one_dict[key] = []

                return

    def _get_pick_one_values(self):
        """
            From the PICK_ONE level onwards, well walk recursivelly appending files according to ends_with
            This path should be equal for every model
        """
        # Only need to explore the levels of one random model
        new_dict:tp.Dict[str, tp.List[Path]] = {}

        for path_prefix in self._pick_one_dict.keys():
            base_path = self.first_non_gt.path.joinpath(path_prefix)
            new_key = base_path.stem
            new_dict[new_key] = []

            for file in self.walk_files_recursive(base_path, self.first_non_gt.path):
                if file.name.endswith(self.gen_ends_with):
                    new_dict[new_key].append(file)

        self._pick_one_dict = new_dict

    def walk_files_recursive(self, path:Path, relative_to:Path):
        """
            Recursively generates all file paths from the given directory path.
        """
        for child in path.iterdir():
            if child.is_dir():
                # If it's a directory, recurse into it and yield results
                yield from self.walk_files_recursive(child, relative_to)
            else:
                # If it's a file (a 'leaf' in the file sense), yield its absolute path
                yield child.relative_to(relative_to)

    def _set_models_paths(self):
        for model in self.models:
            for key, values in self._pick_one_dict.items():
                for value in values:
                    model_content_path = model.path.joinpath(value).relative_to(self.src_dir)
                    model.contents.append(model_content_path)