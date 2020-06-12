import fire
import gpt_2_simple as gpt2
import os


def encode(
    directory='repositories',
    out_path='repositories.npz',
    variant='345M',
):
    # ensure dataset directory exists
    if not os.path.isdir(directory):
        raise AssertionError(f'"{directory}" is not a directory.')

    # encode dataset
    gpt2.encode_dataset(
        directory,
        model_dir='models',
        out_path=out_path,
        model_name=variant,
        combine=50_000,
    )


if __name__ == '__main__':
    fire.Fire(encode)
