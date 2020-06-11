import fire
import gpt_2_simple as gpt2
import os
import requests


def train(
    variant='124M',
    dataset='dataset.npz',
    steps=10_000,
):
    # ensure pretrained gpt-2 variant is downloaded locally
    if not os.path.isdir(os.path.join('models', variant)):
        print(f'Downloading {variant} model...')
        gpt2.download_gpt2(model_name=variant)

    # ensure dataset is already encoded
    if not os.path.isfile(dataset):
        raise FileNotFoundError(f'{dataset} is not found.')

    # start GPT-2 finetuning
    sess = gpt2.start_tf_sess()
    gpt2.finetune(
        sess,
        dataset=dataset,
        model_name=variant,
        steps=steps,
        restore_from='latest',
        run_name='run1',
        print_every=10,
        sample_every=1_000,
        save_every=500,
        overwrite=True,
    )


if __name__ == '__main__':
    fire.Fire(train)
