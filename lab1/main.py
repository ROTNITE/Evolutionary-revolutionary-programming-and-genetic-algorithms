#!/usr/bin/env python3
"""
Лабораторная работа № 1.
Многомерная оптимизация сложной функции генетическим алгоритмом.

Функция Растригина (строка V=3 методички); индивидуально заданная размерность d=5+(22 mod 6)=9.
Ключевые операторы генетического алгоритма реализованы самостоятельно.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np


@dataclass(frozen=True)
class GAConfig:
    dimension: int = 9
    lower_bound: float = -5.12
    upper_bound: float = 5.12
    population_size: int = 80
    generations: int = 250
    tournament_size: int = 3
    crossover_probability: float = 0.90
    blx_alpha: float = 0.50
    mutation_probability: float = 1.0 / 18.0
    mutation_sigma_start: float = 2.50
    mutation_sigma_end: float = 0.03
    elite_count: int = 2

    @property
    def evaluation_budget(self) -> int:
        # Первое поколение оценивается целиком, затем оцениваются только новые потомки.
        return self.population_size + (
            self.generations - 1
        ) * (self.population_size - self.elite_count)


def rastrigin(population: np.ndarray) -> np.ndarray:
    """Векторизованная функция Растригина для массива shape=(n, d)."""
    population = np.asarray(population, dtype=float)
    if population.ndim == 1:
        population = population.reshape(1, -1)
    d = population.shape[1]
    return 10.0 * d + np.sum(
        population**2 - 10.0 * np.cos(2.0 * np.pi * population),
        axis=1,
    )


def initialize_population(config: GAConfig, rng: np.random.Generator) -> np.ndarray:
    return rng.uniform(
        config.lower_bound,
        config.upper_bound,
        size=(config.population_size, config.dimension),
    )


def tournament_indices(
    fitness: np.ndarray,
    count: int,
    tournament_size: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Индексы победителей независимых турниров (задача минимизации)."""
    candidates = rng.integers(
        0,
        len(fitness),
        size=(count, tournament_size),
    )
    candidate_fitness = fitness[candidates]
    winner_positions = np.argmin(candidate_fitness, axis=1)
    return candidates[np.arange(count), winner_positions]


def blx_alpha_crossover(
    parent_a: np.ndarray,
    parent_b: np.ndarray,
    alpha: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """BLX-alpha для двух наборов вещественных родителей."""
    low_parent = np.minimum(parent_a, parent_b)
    high_parent = np.maximum(parent_a, parent_b)
    interval = high_parent - low_parent
    low = low_parent - alpha * interval
    high = high_parent + alpha * interval
    return rng.uniform(low, high)


def gaussian_mutation(
    children: np.ndarray,
    probability: float,
    sigma: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Независимая гауссовская мутация каждой координаты."""
    mask = rng.random(children.shape) < probability
    noise = rng.normal(0.0, sigma, size=children.shape)
    return children + mask * noise


def repair_bounds(children: np.ndarray, config: GAConfig) -> np.ndarray:
    """Ремонт ограничений: отсечение координат по границам области."""
    return np.clip(children, config.lower_bound, config.upper_bound)


def mutation_sigma(config: GAConfig, generation: int) -> float:
    """Экспоненциальное уменьшение масштаба мутации."""
    if config.generations <= 1:
        return config.mutation_sigma_end
    progress = generation / (config.generations - 1)
    ratio = config.mutation_sigma_end / config.mutation_sigma_start
    return config.mutation_sigma_start * (ratio**progress)


def run_ga(seed: int, config: GAConfig) -> dict:
    rng = np.random.default_rng(seed)
    population = initialize_population(config, rng)
    fitness = rastrigin(population)
    evaluations = config.population_size

    best_index = int(np.argmin(fitness))
    best_value = float(fitness[best_index])
    best_vector = population[best_index].copy()
    trajectory = [best_value]

    child_count = config.population_size - config.elite_count

    for generation in range(1, config.generations):
        elite_indices = np.argsort(fitness)[: config.elite_count]
        elites = population[elite_indices].copy()
        elite_fitness = fitness[elite_indices].copy()

        parent_indices = tournament_indices(
            fitness,
            count=2 * child_count,
            tournament_size=config.tournament_size,
            rng=rng,
        )
        parent_a = population[parent_indices[:child_count]]
        parent_b = population[parent_indices[child_count:]]

        do_crossover = rng.random(child_count) < config.crossover_probability
        children = blx_alpha_crossover(
            parent_a,
            parent_b,
            config.blx_alpha,
            rng,
        )
        children[~do_crossover] = parent_a[~do_crossover]

        sigma = mutation_sigma(config, generation)
        children = gaussian_mutation(
            children,
            config.mutation_probability,
            sigma,
            rng,
        )
        children = repair_bounds(children, config)

        child_fitness = rastrigin(children)
        evaluations += child_count

        population = np.vstack((elites, children))
        fitness = np.concatenate((elite_fitness, child_fitness))

        generation_best_index = int(np.argmin(fitness))
        generation_best_value = float(fitness[generation_best_index])
        if generation_best_value < best_value:
            best_value = generation_best_value
            best_vector = population[generation_best_index].copy()

        trajectory.append(best_value)

    return {
        "seed": seed,
        "algorithm": "GA",
        "final_best": best_value,
        "best_vector": best_vector,
        "trajectory": np.asarray(trajectory, dtype=float),
        "evaluations": evaluations,
    }


def run_random_search(seed: int, config: GAConfig) -> dict:
    """
    Случайный поиск с тем же бюджетом вычислений функции.
    Для сопоставимости траектория содержит столько же точек, сколько поколений ГА.
    """
    rng = np.random.default_rng(seed)
    initial = rng.uniform(
        config.lower_bound,
        config.upper_bound,
        size=(config.population_size, config.dimension),
    )
    values = rastrigin(initial)
    evaluations = config.population_size

    best_index = int(np.argmin(values))
    best_value = float(values[best_index])
    best_vector = initial[best_index].copy()
    trajectory = [best_value]

    batch = config.population_size - config.elite_count
    for _ in range(1, config.generations):
        points = rng.uniform(
            config.lower_bound,
            config.upper_bound,
            size=(batch, config.dimension),
        )
        values = rastrigin(points)
        evaluations += batch
        index = int(np.argmin(values))
        if float(values[index]) < best_value:
            best_value = float(values[index])
            best_vector = points[index].copy()
        trajectory.append(best_value)

    return {
        "seed": seed,
        "algorithm": "Random search",
        "final_best": best_value,
        "best_vector": best_vector,
        "trajectory": np.asarray(trajectory, dtype=float),
        "evaluations": evaluations,
    }


def summary(values: Iterable[float]) -> dict:
    array = np.asarray(list(values), dtype=float)
    return {
        "best": float(np.min(array)),
        "mean": float(np.mean(array)),
        "median": float(np.median(array)),
        "std": float(np.std(array, ddof=1)),
        "worst": float(np.max(array)),
    }


def save_runs_csv(path: Path, labeled_runs: list[tuple[str, dict]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        header = [
            "configuration",
            "algorithm",
            "seed",
            "evaluations",
            "final_best",
        ] + [f"x{i}" for i in range(1, labeled_runs[0][1]["best_vector"].size + 1)]
        writer.writerow(header)
        for label, run in labeled_runs:
            writer.writerow(
                [
                    label,
                    run["algorithm"],
                    run["seed"],
                    run["evaluations"],
                    f'{run["final_best"]:.15g}',
                    *[f"{x:.15g}" for x in run["best_vector"]],
                ]
            )


def save_trajectories_csv(path: Path, labeled_runs: list[tuple[str, dict]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["configuration", "seed", "generation", "best_so_far"])
        for label, run in labeled_runs:
            for generation, value in enumerate(run["trajectory"]):
                writer.writerow(
                    [label, run["seed"], generation, f"{value:.15g}"]
                )


def plot_primary_convergence(runs: list[dict], path: Path) -> None:
    trajectories = np.vstack([run["trajectory"] for run in runs])
    minimum = np.min(trajectories, axis=0)
    mean = np.mean(trajectories, axis=0)
    maximum = np.max(trajectories, axis=0)
    generations = np.arange(trajectories.shape[1])

    plt.figure(figsize=(8.2, 4.8))
    plt.plot(generations, np.maximum(minimum, 1e-12), label="Минимум по 20 запускам")
    plt.plot(generations, np.maximum(mean, 1e-12), label="Среднее по 20 запускам")
    plt.plot(generations, np.maximum(maximum, 1e-12), label="Максимум по 20 запускам")
    plt.yscale("log")
    plt.xlabel("Поколение")
    plt.ylabel("Лучшее f(x) на текущий момент, лог. шкала")
    plt.title("Сходимость ГА: функция Растригина, d=9")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_mean_comparison(
    low_mutation_runs: list[dict],
    high_mutation_runs: list[dict],
    random_runs: list[dict],
    path: Path,
) -> None:
    generations = np.arange(len(low_mutation_runs[0]["trajectory"]))
    low_mean = np.mean(
        np.vstack([run["trajectory"] for run in low_mutation_runs]),
        axis=0,
    )
    high_mean = np.mean(
        np.vstack([run["trajectory"] for run in high_mutation_runs]),
        axis=0,
    )
    random_mean = np.mean(
        np.vstack([run["trajectory"] for run in random_runs]),
        axis=0,
    )

    plt.figure(figsize=(8.2, 4.8))
    plt.plot(generations, np.maximum(low_mean, 1e-12), label="ГА: p_mut = 1/(2d)")
    plt.plot(generations, np.maximum(high_mean, 1e-12), label="ГА: p_mut = 2/d")
    plt.plot(generations, np.maximum(random_mean, 1e-12), label="Случайный поиск")
    plt.yscale("log")
    plt.xlabel("Поколение / эквивалентный пакет оценок")
    plt.ylabel("Среднее лучшее f(x), лог. шкала")
    plt.title("Сравнение конфигураций и случайного поиска")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_final_boxplot(
    low_mutation_runs: list[dict],
    high_mutation_runs: list[dict],
    random_runs: list[dict],
    path: Path,
) -> None:
    data = [
        [run["final_best"] for run in low_mutation_runs],
        [run["final_best"] for run in high_mutation_runs],
        [run["final_best"] for run in random_runs],
    ]
    plt.figure(figsize=(7.8, 4.8))
    plt.boxplot(data, tick_labels=["ГА: p=1/(2d)", "ГА: p=2/d", "Случайный поиск"])
    plt.ylabel("Итоговое лучшее значение f(x)")
    plt.title("Распределение результатов 20 независимых запусков")
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_flowchart(path: Path) -> None:
    stages = [
        (0.50, 0.92, "Инициализация\nпопуляции"),
        (0.50, 0.79, "Оценка f(x)"),
        (0.50, 0.66, "Турнирный отбор\nродителей"),
        (0.50, 0.53, "BLX-α кроссовер"),
        (0.50, 0.40, "Гауссовская мутация\n+ repair границ"),
        (0.50, 0.27, "Элитизм и формирование\nнового поколения"),
        (0.50, 0.14, "Критерий останова?"),
    ]

    plt.figure(figsize=(5.8, 8.0))
    ax = plt.gca()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    for x, y, label in stages:
        ax.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            bbox=dict(boxstyle="round,pad=0.45"),
        )

    for i in range(len(stages) - 1):
        ax.annotate(
            "",
            xy=(stages[i + 1][0], stages[i + 1][1] + 0.045),
            xytext=(stages[i][0], stages[i][1] - 0.045),
            arrowprops=dict(arrowstyle="->"),
        )

    ax.annotate(
        "нет",
        xy=(0.40, 0.79),
        xytext=(0.12, 0.25),
        ha="center",
        va="center",
        arrowprops=dict(
            arrowstyle="->",
            connectionstyle="arc3,rad=-0.35",
        ),
    )
    ax.annotate(
        "да",
        xy=(0.50, 0.045),
        xytext=(0.50, 0.095),
        ha="center",
        va="center",
        arrowprops=dict(arrowstyle="->"),
    )
    ax.text(
        0.50,
        0.025,
        "Возврат best-ever",
        ha="center",
        va="center",
        bbox=dict(boxstyle="round,pad=0.35"),
    )

    plt.title("Схема генетического алгоритма")
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def run_experiment(output_dir: Path, runs_count: int, seed_base: int) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)

    config_low = GAConfig(mutation_probability=1.0 / (2.0 * 9.0))
    config_high = GAConfig(mutation_probability=2.0 / 9.0)

    seeds = [seed_base + i for i in range(runs_count)]

    low_runs = [run_ga(seed, config_low) for seed in seeds]
    high_runs = [run_ga(seed, config_high) for seed in seeds]
    random_runs = [run_random_search(seed, config_low) for seed in seeds]

    labeled_runs: list[tuple[str, dict]] = []
    labeled_runs.extend(("GA_low_mutation", run) for run in low_runs)
    labeled_runs.extend(("GA_high_mutation", run) for run in high_runs)
    labeled_runs.extend(("random_search", run) for run in random_runs)

    save_runs_csv(output_dir / "runs.csv", labeled_runs)
    save_trajectories_csv(output_dir / "trajectories.csv", labeled_runs)

    summaries = {
        "variant": "Rastrigin (method row 3); user-specified dimension 9",
        "function": "Rastrigin",
        "dimension": config_low.dimension,
        "theoretical_minimum": 0.0,
        "evaluation_budget": config_low.evaluation_budget,
        "runs_per_configuration": runs_count,
        "seed_base": seed_base,
        "GA_low_mutation": {
            "mutation_probability": config_low.mutation_probability,
            **summary(run["final_best"] for run in low_runs),
        },
        "GA_high_mutation": {
            "mutation_probability": config_high.mutation_probability,
            **summary(run["final_best"] for run in high_runs),
        },
        "random_search": summary(run["final_best"] for run in random_runs),
    }

    best_run = min(low_runs, key=lambda run: run["final_best"])
    summaries["best_run"] = {
        "seed": best_run["seed"],
        "value": best_run["final_best"],
        "vector": [float(x) for x in best_run["best_vector"]],
    }

    with (output_dir / "summary.json").open("w", encoding="utf-8") as file:
        json.dump(summaries, file, ensure_ascii=False, indent=2)

    parameters = {
        "variant": "Rastrigin (method row 3); user-specified dimension 9",
        "dimension_formula": "d = 5 + (22 mod 6) = 9; the number 22 is NOT a formal V in the methods (V=1..20)",
        "variant_note": "Rastrigin is from row V=3; dimension 9 was separately requested",
        "dimension": config_low.dimension,
        "bounds": [config_low.lower_bound, config_low.upper_bound],
        "population_size": config_low.population_size,
        "generations": config_low.generations,
        "evaluation_budget": config_low.evaluation_budget,
        "tournament_size": config_low.tournament_size,
        "crossover": "BLX-alpha",
        "crossover_probability": config_low.crossover_probability,
        "blx_alpha": config_low.blx_alpha,
        "mutation": "Gaussian, per coordinate",
        "mutation_probability_primary": config_low.mutation_probability,
        "mutation_probability_comparison": config_high.mutation_probability,
        "mutation_sigma_start": config_low.mutation_sigma_start,
        "mutation_sigma_end": config_low.mutation_sigma_end,
        "mutation_sigma_schedule": "exponential decay",
        "bounds_handling": "clip",
        "elitism": config_low.elite_count,
        "selection": "tournament, k=3",
        "independent_runs": runs_count,
        "seed_base": seed_base,
    }
    with (output_dir / "parameters.json").open("w", encoding="utf-8") as file:
        json.dump(parameters, file, ensure_ascii=False, indent=2)

    plot_primary_convergence(low_runs, output_dir / "convergence_primary.png")
    plot_mean_comparison(
        low_runs,
        high_runs,
        random_runs,
        output_dir / "comparison_mean.png",
    )
    plot_final_boxplot(
        low_runs,
        high_runs,
        random_runs,
        output_dir / "final_boxplot.png",
    )
    plot_flowchart(output_dir / "flowchart.png")

    return summaries


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results"),
        help="Каталог результатов эксперимента.",
    )
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--seed-base", type=int, default=2026100200)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summaries = run_experiment(args.output_dir, args.runs, args.seed_base)
    print(json.dumps(summaries, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
