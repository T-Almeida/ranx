from typing import List

import numpy as np
from numba import njit, prange
from numba.typed import List as TypedList

from ..data_structures import Run
from .common import (
    convert_results_dict_list_to_run,
    create_empty_results_dict,
    create_empty_results_dict_list,
)
from .isr import _isr_score_parallel


# LOW LEVEL FUNCTIONS ==========================================================
@njit(cache=True)
def _log_comb_mnz(results):
    combined_results = create_empty_results_dict()

    for res in results:
        for doc_id in res.keys():
            if combined_results.get(doc_id, False) == False:
                scores = np.array(
                    [res[doc_id] for res in results if doc_id in res]
                )
                combined_results[doc_id] = sum(scores) * np.log(len(scores))

    return combined_results


@njit(cache=True, parallel=True)
def _log_comb_mnz_parallel(runs):
    q_ids = TypedList(runs[0].keys())
    combined_results = create_empty_results_dict_list(len(q_ids))

    for i in prange(len(q_ids)):
        q_id = q_ids[i]
        combined_results[i] = _log_comb_mnz([run[q_id] for run in runs])

    return convert_results_dict_list_to_run(q_ids, combined_results)


# HIGH LEVEL FUNCTIONS =========================================================
def log_isr(runs: List[Run], name: str = "log_isr") -> Run:
    r"""Computes Log_ISR as proposed by [Mourão et al.](https://www.sciencedirect.com/science/article/abs/pii/S0895611114000664).

    ```bibtex
         @article{DBLP:journals/cmig/MouraoMM15,
            author    = {Andr{\'{e}} Mour{\~{a}}o and
                        Fl{\'{a}}vio Martins and
                        Jo{\~{a}}o Magalh{\~{a}}es},
            title     = {Multimodal medical information retrieval with unsupervised rank fusion},
            journal   = {Comput. Medical Imaging Graph.},
            volume    = {39},
            pages     = {35--45},
            year      = {2015},
            url       = {https://doi.org/10.1016/j.compmedimag.2014.05.006},
            doi       = {10.1016/j.compmedimag.2014.05.006},
            timestamp = {Thu, 14 May 2020 10:17:16 +0200},
            biburl    = {https://dblp.org/rec/journals/cmig/MouraoMM15.bib},
            bibsource = {dblp computer science bibliography, https://dblp.org}
        }
    ```

    Args:
        runs (List[Run]): List of Runs.
        name (str): Name for the combined run. Defaults to "log_isr".

    Returns:
        Run: Combined run.

    """
    _runs = TypedList([_isr_score_parallel(run.run) for run in runs])

    run = Run()
    run.run = _log_comb_mnz_parallel(_runs)
    run.sort()
    run.name = name

    return run
