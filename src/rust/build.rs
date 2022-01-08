use std::env;
use std::fs;
use std::path::{Path, MAIN_SEPARATOR};
use std::process::Command;

use pyo3_build_config::InterpreterConfig;

fn main() {
    let target = env::var("TARGET").unwrap();
    let openssl_static = env::var("OPENSSL_STATIC")
        .map(|x| x == "1")
        .unwrap_or(false);
    if target.contains("apple") && openssl_static {
        // On (older) OSX we need to link against the clang runtime,
        // which is hidden in some non-default path.
        //
        // More details at https://github.com/alexcrichton/curl-rust/issues/279.
        if let Some(path) = macos_link_search_path() {
            println!("cargo:rustc-link-lib=clang_rt.osx");
            println!("cargo:rustc-link-search={}", path);
        }
    }

    let pyo3_interpreter =
        InterpreterConfig::from_pyo3_export_config().expect("could not find pyo3 interpreter");

    let out_dir = env::var("OUT_DIR").unwrap();

    let python_path = match env::var("PYTHONPATH") {
        Ok(mut val) => {
            if cfg!(target_os = "windows") {
                val.push(';');
            } else {
                val.push(':');
            }
            val.push_str(&format!("..{}", MAIN_SEPARATOR));
            val
        }
        Err(_) => format!("..{}", MAIN_SEPARATOR),
    };

    println!("cargo:rerun-if-changed=../_cffi_src/");
    pyo3_interpreter
        .run_python_script_with_envs(
            &fs::read_to_string("../_cffi_src/build_openssl.py")
                .expect("failed to read build_openssl.py"),
            [("PYTHONPATH", python_path), ("OUT_DIR", out_dir.clone())],
        )
        .expect("failed to execute build_openssl.py");

    let python_impl = pyo3_interpreter.implementation.to_string();
    let python_include = pyo3_interpreter
        .run_python_script("import sysconfig; print(sysconfig.get_path('include'), end='')")
        .unwrap();
    let openssl_include =
        std::env::var_os("DEP_OPENSSL_INCLUDE").expect("unable to find openssl include path");
    let openssl_c = Path::new(&out_dir).join("_openssl.c");

    let mut build = cc::Build::new();
    build
        .file(openssl_c)
        .include(python_include)
        .include(openssl_include)
        .flag_if_supported("-Wconversion")
        .flag_if_supported("-Wno-error=sign-conversion");

    // Enable abi3 mode if we're not using PyPy.
    if python_impl != "PyPy" {
        // cp36
        // build.define("Py_LIMITED_API", "0x030600f0");
    }

    if cfg!(windows) {
        build.define("WIN32_LEAN_AND_MEAN", None);
    }

    build.compile("_openssl.a");
}

fn macos_link_search_path() -> Option<String> {
    let output = Command::new("clang")
        .arg("--print-search-dirs")
        .output()
        .ok()?;
    if !output.status.success() {
        println!(
            "failed to run 'clang --print-search-dirs', continuing without a link search path"
        );
        return None;
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    for line in stdout.lines() {
        if line.contains("libraries: =") {
            let path = line.split('=').nth(1)?;
            return Some(format!("{}/lib/darwin", path));
        }
    }

    println!("failed to determine link search path, continuing without it");
    None
}
