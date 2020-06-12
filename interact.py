import codecs
import fire
import gpt_2_simple as gpt2
import os


def interact(src=None, variant='345M'):
    # attempt to read file if src is not given
    if src is None:
        raise AssertionError(f'input "src" should not be None')

    # treat src as src file if it is a file
    if os.path.isfile(src):
        with codecs.open(src, 'r', 'utf-8') as f:
            src = f.read()
            
    # initialize pretrained model for code generation
    sess = gpt2.start_tf_sess()
    gpt2.load_gpt2(sess, model_name=variant)

    # run generation task
    output = gpt2.generate(
        sess,
        prefix=src,
        length=20,
        model_name=variant,
        return_as_list=True,
    )[0]

    print(f'{"="*40} OUTPUT {"="*40}')
    print(output)
    print('=' * 88)


if __name__ == '__main__':
    fire.Fire(interact)