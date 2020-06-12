from tqdm import tqdm

import codecs
import csv
import fire
import os
import re
import requests
import shutil


API_BASE_URL = 'https://api.github.com'
REPO_INFO_API = '/repos/{}/{}'
REPO_ZIP_URL = 'https://github.com/{}/{}/archive/{}.zip'
EXCLUDED_PATTERN = re.compile(r'(?:__init__\.py)|(?:test_.+\.py)')


def download_dataset(
    name='repositories.csv',
    star_count_threshold=1000,
    access_token=None,
    start_from_scratch=True,
):
    repositories = get_repo_list()
    pbar = tqdm(repositories)

    # delete repositories so that it's clean
    if start_from_scratch and os.path.isdir('repositories'):
        shutil.rmtree('repositories')

    for user, name in pbar:
        try:
            collate_python_files(
                user=user,
                name=name,
                access_token=None
            )
        except OSError as e:
            pbar.write('WARN - Could not unpack {}/{}'.format(user, name))
            pbar.write(str(e))

    # delete temporary directory
    if os.path.isdir('tmp'):
        shutil.rmtree('tmp')


def get_repo_list(
    filename='repositories.csv',
    star_count_threshold=1000
):
    # ensure csv file exists
    if not os.path.isfile(filename):
        raise FileNotFoundError(f'"{filename}" does not exist.')

    # the resulting repository list container
    repositories = []

    # csv file should be opened using UTF8 encoding
    # since repository names may contain non-ASCII letters
    with codecs.open(filename, 'r', 'utf8', errors='replace') as fd:
        reader = csv.reader(fd, delimiter=',')

        # skip first line of csv file since it only contains headers
        next(reader)

        for repo_name, repo_stars in reader:
            if int(repo_stars) >= star_count_threshold:
                user, name = repo_name.split('/')
                repositories.append((user, name))
            else:
                # star count is already below the threshold
                # that is, all of the subsequent repositories
                # will have a star count below the threshold
                break

    return repositories


def collate_python_files(user, name, access_token=None):
    # ensure "repositories" directory exists
    if not os.path.isdir('repositories'):
        os.mkdir('repositories')

    # ensure parent directory for the user exists
    user_dir = os.path.join('repositories', user)
    if not os.path.isdir(user_dir):
        os.mkdir(user_dir)

    # ensure temporary directory exists
    if not os.path.isdir('tmp'):
        os.mkdir('tmp')

    # skip if repository is already downloaded and extracted
    container_dir = os.path.join('repositories', user, name)
    if os.path.isdir(container_dir):
        return

    # create pathname for the to-be-downloaded tarball
    zip_filename = '{}_{}.zip'.format(user, name)
    output_path = os.path.join('tmp', zip_filename)
    download_latest_release(user, name, output_path, access_token=access_token)
    extract_python_src_files(user, name, output_path)


def get_latest_release_tarball_url(user, name, access_token=None):
    """
    Retrieves the download url of the repository as a compressed zip file.
    The downloaded zip file will contain the latest code of the 
    default branch of the repository. Only repositories in Github are supported.

    Parameters:
    user (string): the username of the owner of the github repository
    name (string): the name of the target repository 

    Returns:
    url (string): the download url of the repository as zip
    """
    latest_release_api = REPO_INFO_API.format(user, name)
    api_url = API_BASE_URL + latest_release_api
    headers = get_header_for_auth(access_token=access_token)
    r = requests.get(api_url, headers=headers)

    # Ensure API requests return OK
    if r.status_code != 200:
        raise AssertionError(r.text)

    # get repo's default branch
    default_branch = r.json()['default_branch']

    # return download link for the source zip
    return REPO_ZIP_URL.format(user, name, default_branch)


def download_latest_release(user, name, path, access_token=None):
    """
    Downloads the github repository at github.com/{user}/{name}
    as a zip. The downloaded zip will contain the latest source code
    of the default branch of the repository. The downloaded file will be placed in path.

    Parameters:
    user (string): the username of the owner of the github repository
    name (string): the name of the target repository 
    path (string): the path in which the downloaded zip file will be written to
    """
    url = get_latest_release_tarball_url(user, name, access_token=access_token)
    r = requests.get(url, stream=True)

    with open(path, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)


def extract_python_src_files(user, repo_name, tarball_path):
    # ensure path exists and ends with ".zip"
    assert os.path.isfile(tarball_path)
    assert tarball_path.endswith('.zip')

    # unpack and delete tarball
    unpack_destination = os.path.join('tmp', user + '_' + repo_name)
    shutil.unpack_archive(tarball_path, unpack_destination)

    # ensure target source files container directory exists
    container_directory = os.path.join('repositories', user, repo_name)
    if not os.path.isdir(container_directory):
        os.mkdir(container_directory)

    # the name of the folder that contains the project code
    # is the repository name plus the version/tag
    project_path = [os.path.join(unpack_destination, f) for f in os.listdir(unpack_destination)
                    if os.path.isdir(os.path.join(unpack_destination, f))][0]

    # move all candidate python source files to the target container directory
    for root, dirs, files in os.walk(project_path):
        # remove all test directories
        for d in dirs:
            if d.startswith('test'):
                shutil.rmtree(os.path.join(root, d))

        for f in files:
            if f.endswith('.py') and not re.match(EXCLUDED_PATTERN, f):
                file_src_path = os.path.join(root, f)
                file_dst_path = os.path.join(container_directory, f)
                shutil.move(file_src_path, file_dst_path)

    # delete zip file and original project directory
    os.remove(tarball_path)
    shutil.rmtree(project_path)


def get_header_for_auth(access_token=None):
    if access_token is None:
        try:
            access_token = os.environ['GITHUB_ACCESS_TOKEN']
        except KeyError:
            err_msg = 'ERROR - "GITHUB_ACCESS_TOKEN" variable not found!'
            raise EnvironmentError(err_msg)

    auth_value = 'token {}'.format(access_token)
    return {'Authorization': auth_value}


if __name__ == '__main__':
    fire.Fire(download_dataset)
